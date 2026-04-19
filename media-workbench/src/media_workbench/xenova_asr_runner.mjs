import fs from "fs";
import path from "path";
import { createRequire } from "module";
import { pathToFileURL } from "url";

function die(message) {
  console.error(message);
  process.exit(1);
}

function resolverFromNodeModules(nodeModules) {
  if (!nodeModules) return createRequire(import.meta.url);
  return createRequire(path.join(nodeModules, "package.json"));
}

async function importPackage(packageName, requireFrom) {
  const resolved = requireFrom.resolve(packageName);
  return import(pathToFileURL(resolved).href);
}

const [, , audioPath, outDir, assetHash] = process.argv;
if (!audioPath || !outDir || !assetHash) {
  die("Usage: node xenova_asr_runner.mjs <audio.wav> <out_dir> <asset_hash>");
}

const modelRoot = process.env.MEDIA_WORKBENCH_XENOVA_MODEL_ROOT;
const modelName = process.env.MEDIA_WORKBENCH_XENOVA_MODEL || "Xenova/whisper-small";
const nodeModules = process.env.MEDIA_WORKBENCH_XENOVA_NODE_MODULES || "";

if (!modelRoot) die("MEDIA_WORKBENCH_XENOVA_MODEL_ROOT is required.");
if (!fs.existsSync(path.join(modelRoot, ...modelName.split("/")))) {
  die(`Xenova model is missing under ${modelRoot}: ${modelName}`);
}

fs.mkdirSync(outDir, { recursive: true });

const requireFrom = resolverFromNodeModules(nodeModules);
const { pipeline, env } = await importPackage("@xenova/transformers", requireFrom);
const { WaveFile } = requireFrom("wavefile");

env.allowRemoteModels = false;

const wav = new WaveFile(fs.readFileSync(audioPath));
wav.toBitDepth("32f");
wav.toSampleRate(16000);

let audioData = wav.getSamples();
if (Array.isArray(audioData)) {
  if (audioData.length > 1) {
    const merged = new Float32Array(audioData[0].length);
    for (let i = 0; i < audioData[0].length; i += 1) {
      merged[i] = (audioData[0][i] + audioData[1][i]) / 2;
    }
    audioData = merged;
  } else {
    audioData = audioData[0];
  }
}
audioData = Float32Array.from(audioData);

const transcriber = await pipeline("automatic-speech-recognition", modelName, {
  cache_dir: modelRoot,
  local_files_only: true,
});
const result = await transcriber(audioData, {
  chunk_length_s: 30,
  stride_length_s: 5,
});

const text = `${(result.text || "").trim()}\n`;
const payload = {
  asset_hash: assetHash,
  engine: "xenova-transformers",
  model: modelName,
  source_path: audioPath,
  text: text.trim(),
  chunks: result.chunks || [],
};

fs.writeFileSync(path.join(outDir, "transcript.txt"), text, "utf-8");
fs.writeFileSync(path.join(outDir, "transcript.json"), `${JSON.stringify(payload, null, 2)}\n`, "utf-8");
fs.writeFileSync(
  path.join(outDir, "transcript.srt"),
  `1\n00:00:00,000 --> 00:00:30,000\n${text.trim()}\n`,
  "utf-8",
);

import type { VanatomeAtlas, VanatomeVector3 } from './vendor/types';

// Shared atlas coordinates; regional topics supply only their structure mappings.
export const modelVersion = 'vanatome-1.4.0-994e6cc8ffbb212e';
export const modelScale = 7;
export const modelPosition: VanatomeVector3 = [0, -6.1, 0];

/** A chapter add-on id (library/<id>/3d/atlas-addon.json); it names files under ./models/. */
export const addonIdPattern = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

type AtlasSource = { id: string; name: string; metadataUrl: string; modelUrl: string; attribution: string; failure: string };

const baseSources: AtlasSource[] = ['muscular', 'skeletal'].map(system => ({
  id: 'vanatome-human-' + system,
  name: 'Vanatome ' + system,
  metadataUrl: `./models/${system}.metadata.json`,
  modelUrl: `./models/z-anatomy-1.4.0-${system}.glb`,
  attribution: 'Z-Anatomy / BodyParts3D · CC BY-SA 4.0 · Vanatome',
  failure: 'Unable to load model metadata / 无法读取模型结构清单',
}));

function addonSource(addon: string): AtlasSource {
  if (!addonIdPattern.test(addon)) throw new Error(`Invalid 3D add-on id “${addon}” / 三维附加模型编号不正确：${addon}`);
  return {
    id: `vanatome-human-${addon}-addon`,
    name: `Vanatome ${addon} add-on`,
    metadataUrl: `./models/${addon}-addon.metadata.json`,
    modelUrl: `./models/z-anatomy-1.4.0-${addon}-addon.glb`,
    attribution: 'Z-Anatomy / BodyParts3D · CC BY-SA 4.0 · Vanatome exporter',
    failure: `Unable to load the ${addon} add-on model metadata / 无法读取 ${addon} 附加模型结构清单`,
  };
}

async function loadAtlas(source: AtlasSource): Promise<VanatomeAtlas> {
  let meta: { atlasVersion?: unknown; buildId?: unknown; structures?: unknown };
  try {
    const res = await fetch(source.metadataUrl);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    meta = await res.json();
  } catch (reason) {
    throw new Error(`${source.failure} (${reason instanceof Error ? reason.message : String(reason)})`);
  }
  if (!meta || typeof meta.atlasVersion !== 'string' || !Array.isArray(meta.structures)) throw new Error(source.failure);
  return {
    id: source.id,
    name: source.name,
    version: meta.atlasVersion,
    buildId: typeof meta.buildId === 'string' ? meta.buildId : undefined,
    modelUrl: source.modelUrl,
    structures: meta.structures,
    attribution: source.attribution,
  };
}

/** The muscular and skeletal atlases, plus one atlas per chapter add-on (same coordinates and build). */
export async function loadAtlases(addons: readonly string[] = []): Promise<VanatomeAtlas[]> {
  const sources = [...baseSources, ...[...new Set(addons)].map(addonSource)];
  return Promise.all(sources.map(loadAtlas));
}

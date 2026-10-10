export type BilingualText = { en: string; zh: string };
export type TopicTerm = {
  id: string;
  name: BilingualText;
  kind: 'bone' | 'muscle';
  structures: { right: string; left: string };
};
export type TopicLandmark = {
  id: string;
  name: BilingualText;
  structures: { right: string; left: string };
  positions?: { right: [number, number, number]; left: [number, number, number] };
  reviewStatus: 'reviewed' | 'pending';
};
export type StudyTopic = {
  id: string;
  title: BilingualText;
  summary: BilingualText;
  status: 'published' | 'draft';
  adapter: 'shoulder' | 'standard';
  /** addons: chapter 3D add-on models the viewer loads (library/<id>/3d/atlas-addon.json; set by the topic build). */
  viewer: { enabled: boolean; defaultTerm: string | null; terms: TopicTerm[]; landmarks?: TopicLandmark[]; addons?: string[] };
  links?: { reading?: string };
};
export type TopicCatalog = { schemaVersion: 1; topics: StudyTopic[] };
const slug = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value));
}
function isBilingual(value: unknown): value is BilingualText {
  return isRecord(value) && typeof value.en === 'string' && value.en.length > 0 && typeof value.zh === 'string' && value.zh.length > 0;
}
function isTerm(value: unknown): value is TopicTerm {
  return isRecord(value) && typeof value.id === 'string' && value.id.length > 0 && isBilingual(value.name)
    && ['bone', 'muscle'].includes(String(value.kind)) && isRecord(value.structures)
    && typeof value.structures.right === 'string' && value.structures.right.length > 0
    && typeof value.structures.left === 'string' && value.structures.left.length > 0;
}
function isPosition(value: unknown): boolean {
  return Array.isArray(value) && value.length === 3 && value.every(coordinate => typeof coordinate === 'number' && Number.isFinite(coordinate));
}
function isLandmark(value: unknown): value is TopicLandmark {
  if (!isRecord(value) || typeof value.id !== 'string' || !value.id || !isBilingual(value.name)
    || !isRecord(value.structures) || typeof value.structures.right !== 'string' || typeof value.structures.left !== 'string'
    || !['reviewed', 'pending'].includes(String(value.reviewStatus))) return false;
  if (value.positions === undefined) return value.reviewStatus === 'pending';
  return isRecord(value.positions) && isPosition(value.positions.right) && isPosition(value.positions.left);
}

export function parseTopicCatalog(value: unknown): TopicCatalog {
  if (!isRecord(value) || value.schemaVersion !== 1 || !Array.isArray(value.topics)) throw new Error('Unsupported topic catalog / 主题目录格式不受支持');
  const ids = new Set<string>();
  for (const item of value.topics) {
    if (!isRecord(item) || typeof item.id !== 'string' || !slug.test(item.id)
      || !isBilingual(item.title) || !isBilingual(item.summary)
      || !['published', 'draft'].includes(String(item.status)) || !['shoulder', 'standard'].includes(String(item.adapter))
      || !isRecord(item.viewer) || typeof item.viewer.enabled !== 'boolean'
      || !(item.viewer.defaultTerm === null || typeof item.viewer.defaultTerm === 'string')
      || !Array.isArray(item.viewer.terms) || !item.viewer.terms.every(isTerm)
      || (item.viewer.landmarks !== undefined && (!Array.isArray(item.viewer.landmarks) || !item.viewer.landmarks.every(isLandmark)))
      || (item.viewer.addons !== undefined && (!Array.isArray(item.viewer.addons) || !item.viewer.addons.every(addon => typeof addon === 'string' && slug.test(addon))))) {
      throw new Error('Incomplete topic configuration / 主题配置不完整');
    }
    if (ids.has(item.id)) throw new Error(`Duplicate topic / 重复主题：${item.id}`);
    ids.add(item.id);
    const termIds = new Set(item.viewer.terms.map(term => term.id));
    if (termIds.size !== item.viewer.terms.length || (item.viewer.defaultTerm !== null && !termIds.has(item.viewer.defaultTerm))) {
      throw new Error(`Invalid topic terms / 主题词条配置不正确：${item.id}`);
    }
    if (Array.isArray(item.viewer.landmarks) && new Set(item.viewer.landmarks.map(landmark => landmark.id)).size !== item.viewer.landmarks.length) {
      throw new Error(`Duplicate landmarks / 重复骨性标志：${item.id}`);
    }
    if (item.links !== undefined && (!isRecord(item.links)
      || (item.links.reading !== undefined && (typeof item.links.reading !== 'string' || !item.links.reading.startsWith('./'))))) {
      throw new Error(`Invalid reading link / 阅读链接不正确：${item.id}`);
    }
  }
  return value as TopicCatalog;
}

export function topicHref(topic: Pick<StudyTopic, 'id' | 'viewer'>): string {
  const query = new URLSearchParams({ topic: topic.id });
  if (topic.viewer.defaultTerm) query.set('term', topic.viewer.defaultTerm);
  return `./?${query}`;
}

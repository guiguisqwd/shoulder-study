import { useEffect, useMemo, useRef, useState } from 'react';
import { loadAtlases, modelPosition, modelScale } from './model';
import type { StudyTopic, TopicLandmark, TopicTerm } from './topics';
import { VanatomeViewer } from './vendor/VanatomeViewer';
import { getRelatedStructureIds } from './vendor/sceneBehavior';
import { fitDockedLabels, useElementHeight, type DockCandidate } from './labelDock';
import type { VanatomeAnnotation, VanatomeAtlas, VanatomeCameraRequest, VanatomeDisplayMode, VanatomeVector3 } from './vendor/types';

type Side = 'right' | 'left';
type View = 'front' | 'back' | 'side';
const views: { id: View; en: string; zh: string }[] = [
  { id: 'front', en: 'Anterior', zh: '前面观' }, { id: 'back', en: 'Posterior', zh: '后面观' }, { id: 'side', en: 'Lateral', zh: '外侧观' },
];
const modes: { id: VanatomeDisplayMode; en: string; zh: string }[] = [
  { id: 'normal', en: 'Solid', zh: '实体' }, { id: 'xray', en: 'X-ray', zh: '透视' }, { id: 'ghost', en: 'Ghost', zh: '淡显' },
];
function directionFor(view: View, side: Side): VanatomeVector3 {
  return view === 'side' ? [side === 'right' ? -1 : 1, 0.08, 0.08] : [side === 'right' ? 0.12 : -0.12, 0.08, view === 'front' ? 1 : -1];
}

/** A new regional topic supplies terms and structure IDs, not another viewer implementation. */
export function StandardTopicViewer({ topic }: { topic: StudyTopic }) {
  const initialQuery = useMemo(() => new URLSearchParams(location.search), []);
  const linkedTerm = initialQuery.get('term');
  const initialSide = initialQuery.get('side') === 'left' ? 'left' : 'right';
  const initialLandmark = topic.viewer.landmarks?.find(item => item.id === initialQuery.get('landmark') && item.reviewStatus === 'reviewed' && item.positions);
  const initialTerm = topic.viewer.terms.find(item => initialLandmark && item.structures[initialSide] === initialLandmark.structures[initialSide])
    || topic.viewer.terms.find(term => term.id === linkedTerm)
    || topic.viewer.terms.find(term => term.id === topic.viewer.defaultTerm) || topic.viewer.terms[0];
  const [atlases, setAtlases] = useState<VanatomeAtlas[]>([]);
  const [error, setError] = useState('');
  const [ready, setReady] = useState(false);
  const [side, setSide] = useState<Side>(initialSide);
  const [termId, setTermId] = useState(initialTerm?.id || '');
  const [view, setView] = useState<View>('front');
  const [freeView, setFreeView] = useState(false);
  const [displayMode, setDisplayMode] = useState<VanatomeDisplayMode>('xray');
  // Only the selected structure is labelled until All labels is ticked (gui, 2026-10-09).
  const [allLabels, setAllLabels] = useState(false);
  const [showChinese, setShowChinese] = useState(true);
  const [bones, setBones] = useState(true);
  const [muscles, setMuscles] = useState(true);
  const [isolate, setIsolate] = useState(false);
  const [showLandmarks, setShowLandmarks] = useState(Boolean(initialLandmark));
  const [landmarkId, setLandmarkId] = useState<string | null>(initialLandmark?.id || null);
  const [cameraRequest, setCameraRequest] = useState<VanatomeCameraRequest | null>(null);
  const requestId = useRef(0);
  const initialFocusDone = useRef(false);
  const sceneRef = useRef<HTMLDivElement>(null);
  const sceneHeight = useElementHeight(sceneRef);
  const structures = useMemo(() => atlases.flatMap(atlas => atlas.structures), [atlases]);
  const structureIndex = useMemo(() => new Map(structures.map(structure => [structure.id, structure])), [structures]);
  const term = topic.viewer.terms.find(item => item.id === termId) || initialTerm;
  const selectedId = term?.structures[side] || null;
  const reviewedLandmarks = useMemo(() => (topic.viewer.landmarks || []).filter(item => item.reviewStatus === 'reviewed' && item.positions), [topic.viewer.landmarks]);
  const selectedLandmark = reviewedLandmarks.find(item => item.id === landmarkId);
  const pendingLandmarkCount = (topic.viewer.landmarks || []).filter(item => item.reviewStatus === 'pending').length;
  const termStructures = useMemo(() => new Map(topic.viewer.terms.map(item => [item.id,
    getRelatedStructureIds(structures, item.structures[side]),
  ])), [topic.viewer.terms, structures, side]);
  const availableTerms = useMemo(() => topic.viewer.terms.filter(item => structures.some(structure =>
    structure.objectCount && termStructures.get(item.id)?.has(structure.id))), [topic.viewer.terms, structures, termStructures]);
  const missingTerms = structures.length ? topic.viewer.terms.filter(item => !availableTerms.includes(item)) : [];
  const visibleTerms = availableTerms.filter(item => (!isolate || item.id === termId) && (item.kind === 'bone' ? bones : muscles));
  const visibleTermIds = visibleTerms.map(item => item.id).join('|');
  const hiddenIds = useMemo(() => {
    const visibleIds = new Set(visibleTermIds.split('|').flatMap(id => [...(termStructures.get(id) || [])]));
    return structures.filter(structure => structure.objectCount && !visibleIds.has(structure.id)).map(structure => structure.id);
  }, [structures, termStructures, visibleTermIds]);
  // Labels dock in a column beside the model; with All labels on and too many to fit, the selection comes first and a note says so.
  const labelLayout = useMemo(() => {
    const candidates: DockCandidate[] = visibleTermIds.split('|').flatMap((id, order): DockCandidate[] => {
      const item = topic.viewer.terms.find(candidate => candidate.id === id);
      const structure = item && structureIndex.get(item.structures[side]);
      if (!item || !structure) return [];
      const position = structure.position.map((value, axis) => (value - modelPosition[axis]) / modelScale) as unknown as VanatomeVector3;
      return [{ annotation: { id: `term:${item.id}`, label: `${item.name.en}${showChinese ? `\n${item.name.zh}` : ''}`, position,
        color: item.kind === 'bone' ? '#dfd2ad' : '#a6cbb9', showLabel: allLabels }, priority: item.id === termId ? 0.5 : 2 + order / 1000, y: position[1] }];
    });
    if (showLandmarks) for (const landmark of reviewedLandmarks) {
      const isVisible = visibleTermIds.split('|').some(id => termStructures.get(id)?.has(landmark.structures[side]));
      if (!isVisible || !landmark.positions || !structureIndex.has(landmark.structures[side])) continue;
      candidates.push({ annotation: { id: `landmark:${landmark.id}`, label: `${landmark.name.en}${showChinese ? `\n${landmark.name.zh}` : ''}`,
        position: landmark.positions[side], color: '#f1c16f', showLabel: allLabels }, priority: landmark.id === landmarkId ? 0 : 1, y: landmark.positions[side][1] });
    }
    // With All labels off, only the selected structure (and a selected landmark) is labelled and marked.
    if (!allLabels) {
      const selected = candidates.filter(item => item.priority <= 0.5).map(item => ({ ...item, annotation: { ...item.annotation, showLabel: true } }));
      return { items: fitDockedLabels(selected, sceneHeight), total: selected.length };
    }
    return { items: fitDockedLabels(candidates, sceneHeight), total: candidates.length };
  }, [visibleTermIds, topic.viewer.terms, structureIndex, side, showChinese, allLabels, showLandmarks, reviewedLandmarks, termStructures, termId, landmarkId, sceneHeight]);
  const annotations = labelLayout.items;
  const initialTarget = useMemo((): VanatomeVector3 => {
    const id = initialTerm?.structures[initialQuery.get('side') === 'left' ? 'left' : 'right'];
    return (id && structureIndex.get(id)?.position) || [0, 0, 0];
  }, [structureIndex, initialTerm, initialQuery]);
  const initialPosition = useMemo((): VanatomeVector3 => [initialTarget[0] + 0.4, initialTarget[1] + 0.3, initialTarget[2] + 5], [initialTarget]);

  const addonKey = (topic.viewer.addons ?? []).join('|');
  useEffect(() => {
    if (!topic.viewer.enabled || !topic.viewer.terms.length) return;
    let active = true;
    // A chapter with its own add-on model (library/<id>/3d/atlas-addon.json) loads it beside the shared models.
    loadAtlases(addonKey ? addonKey.split('|') : []).then(data => { if (active) setAtlases(data); }).catch(reason => { if (active) setError(String(reason)); });
    return () => { active = false; };
  }, [topic.viewer.enabled, topic.viewer.terms.length, addonKey]);
  useEffect(() => {
    if (!ready || initialFocusDone.current || !selectedId || !availableTerms.some(item => item.id === termId)) return;
    initialFocusDone.current = true;
    setCameraRequest(selectedLandmark?.positions
      ? { id: ++requestId.current, kind: 'point', target: selectedLandmark.positions[side], direction: directionFor('front', side), distance: 2.5 }
      : { id: ++requestId.current, kind: 'structure', structureId: selectedId, direction: directionFor('front', side), distance: 2.5 });
  }, [ready, selectedId, side, termId, availableTerms, selectedLandmark]);

  function updateLink(nextTerm: string, nextSide = side, nextLandmark?: string) {
    const url = new URL(location.href);
    url.searchParams.set('topic', topic.id);
    url.searchParams.set('term', nextTerm);
    url.searchParams.set('side', nextSide);
    url.searchParams.delete('point');
    if (nextLandmark) url.searchParams.set('landmark', nextLandmark); else url.searchParams.delete('landmark');
    history.replaceState(null, '', url);
  }
  function selectTerm(next: TopicTerm) {
    if (!availableTerms.includes(next)) return;
    setTermId(next.id);
    setLandmarkId(null);
    if (next.kind === 'bone') setBones(true); else setMuscles(true);
    updateLink(next.id);
    // Deliberate focus preserves the user's viewing direction; layer/label changes never move it.
    setCameraRequest({ id: ++requestId.current, kind: 'structure', structureId: next.structures[side], distance: 2.5 });
  }
  function selectLandmark(next: TopicLandmark) {
    if (next.reviewStatus !== 'reviewed' || !next.positions) return;
    const associatedTerm = availableTerms.find(item => termStructures.get(item.id)?.has(next.structures[side]));
    if (!associatedTerm) return;
    setTermId(associatedTerm.id); setLandmarkId(next.id); setShowLandmarks(true);
    if (associatedTerm.kind === 'bone') setBones(true); else setMuscles(true);
    updateLink(associatedTerm.id, side, next.id);
    setCameraRequest({ id: ++requestId.current, kind: 'point', target: next.positions[side],
      preserveDistance: associatedTerm.id === termId, distance: 2.5 });
  }
  function changeSide(nextSide: Side) {
    if (nextSide === side) return;
    setSide(nextSide);
    if (term) {
      updateLink(term.id, nextSide, selectedLandmark?.id);
      const direction = view === 'side' && !freeView ? directionFor(view, nextSide) : undefined;
      setCameraRequest(selectedLandmark?.positions
        ? { id: ++requestId.current, kind: 'point', target: selectedLandmark.positions[nextSide], preserveDistance: true, direction }
        : { id: ++requestId.current, kind: 'structure', structureId: term.structures[nextSide], preserveDistance: true, direction });
    }
  }
  function changeView(next: View) {
    setView(next); setFreeView(false);
    setCameraRequest({ id: ++requestId.current, kind: 'orbit', direction: directionFor(next, side) });
  }

  return <div className="app standard-topic">
    <header className="masthead"><div><span className="eyebrow">ANATOMY · SPATIAL STUDY</span><h1>{topic.title.en}<span>{topic.title.zh}</span></h1></div>
      {topic.links?.reading && <a className="reading-link" href={topic.links.reading}>Reading notes · 阅读笔记 ↗</a>}
    </header>
    {topic.status === 'draft' && <div className="topic-preview-notice"><strong>Model preview · 模型预览</strong><span>Learning content awaits review. · 教学内容待核对。</span></div>}
    {!topic.viewer.enabled || !topic.viewer.terms.length ? <main className="topic-empty"><h2>Viewer not configured · 三维内容待配置</h2><p>{topic.summary.en}</p><p>{topic.summary.zh}</p><a href="./study.html">All topics · 全部主题 →</a></main>
      : <main className="workspace">
        <section className="viewer-panel" aria-label={`${topic.title.en} 3D anatomy`}>
          <div className="toolbar"><div className="segments">{(['right', 'left'] as const).map(value => <button key={value} aria-pressed={side === value} onClick={() => changeSide(value)}>{value === 'right' ? 'Right · 右侧' : 'Left · 左侧'}</button>)}</div>
            <div className="segments">{views.map(item => <button key={item.id} aria-pressed={view === item.id && !freeView} onClick={() => changeView(item.id)}>{item.en}<small>{item.zh}</small></button>)}</div></div>
          <div ref={sceneRef} className="scene">
            {atlases.length > 0 && !error && <VanatomeViewer atlases={atlases} modelScale={modelScale} modelPosition={modelPosition}
              initialCameraTarget={initialTarget} initialCameraPosition={initialPosition} cameraRequest={cameraRequest}
              enablePan minDistance={0.7} maxDistance={28} focusDistance={2.5} hiddenIds={hiddenIds}
              selectedId={selectedId} displayMode={displayMode} annotations={annotations} selectedAnnotationId={landmarkId ? `landmark:${landmarkId}` : `term:${termId}`}
              onAnnotationSelect={id => {
                if (id.startsWith('landmark:')) { const next = reviewedLandmarks.find(item => item.id === id.slice(9)); if (next) selectLandmark(next); }
                else { const next = topic.viewer.terms.find(item => `term:${item.id}` === id); if (next) selectTerm(next); }
              }}
              onSelect={id => { const next = availableTerms.find(item => id && termStructures.get(item.id)?.has(id)); if (next) selectTerm(next); }}
              onReady={() => setReady(true)} onError={issue => setError(issue.message)} onInteractionStart={() => setFreeView(true)}
              appearance={{ xrayOpacity: 0.32, ghostOpacity: 0.13, pulseSelection: false, skeletonId: 'skeletal-system', bodyShellId: null }}
              loadingFallback={<div className="loading">Loading anatomy model… · 正在载入解剖模型…</div>}
              ariaLabel={`${topic.title.en} · ${topic.title.zh}`} />}
            {error && <div className="loading" role="alert">Model unavailable · 模型无法载入<p>{error}</p><button onClick={() => location.reload()}>Retry · 重试</button></div>}
            {!atlases.length && !error && <div className="loading">Loading anatomy model… · 正在载入解剖模型…</div>}
            <div className="scene-caption"><span className="live-dot" />{term?.name.en}{showChinese && term ? ` · ${term.name.zh}` : ''}</div>
            <div className="scene-help">Drag to rotate · Scroll to zoom<br />拖动旋转 · 滚动缩放</div>
            <div className={`orientation${allLabels && annotations.length > 8 ? ' beside-dock' : ''}`}>{side === 'right' ? 'R' : 'L'}<small>{freeView ? 'Free view · 自由视角' : views.find(item => item.id === view)?.en}</small></div>
          </div>
          {allLabels && labelLayout.items.length < labelLayout.total && <p className="label-note" role="status">{labelLayout.items.length} of {labelLayout.total} labels fit the view; select a structure or tick Isolate selection to see the rest. · 视图中可显示 {labelLayout.items.length}/{labelLayout.total} 个标注；点选结构或勾选“单独显示”可查看其余名称。</p>}
          <div className="layerbar"><div className="segments">{modes.map(mode => <button key={mode.id} aria-pressed={displayMode === mode.id} onClick={() => setDisplayMode(mode.id)}>{mode.en}<small>{mode.zh}</small></button>)}</div>
            {topic.viewer.terms.some(item => item.kind === 'bone') && <label><input type="checkbox" checked={bones} onChange={event => setBones(event.target.checked)} />Bones · 骨骼</label>}
            {topic.viewer.terms.some(item => item.kind === 'muscle') && <label><input type="checkbox" checked={muscles} onChange={event => setMuscles(event.target.checked)} />Muscles · 肌肉</label>}
          </div>
          <div className="annotation-options"><label><input type="checkbox" checked={allLabels} onChange={event => setAllLabels(event.target.checked)} />All labels · 全部标注</label>
            <label><input type="checkbox" checked={showChinese} onChange={event => setShowChinese(event.target.checked)} />Chinese translation · 中文释义</label>
            <label><input type="checkbox" checked={isolate} onChange={event => setIsolate(event.target.checked)} />Isolate selection · 单独显示</label>
            {reviewedLandmarks.length > 0 && <label><input type="checkbox" checked={showLandmarks} onChange={event => { setShowLandmarks(event.target.checked); if (!event.target.checked) setLandmarkId(null); }} />Bone landmarks · 骨性标志</label>}
            <button disabled={!ready || !term || !availableTerms.includes(term)} onClick={() => { if (term) selectTerm(term); }}>Fit selection · 适配视野</button>
          </div>
          {missingTerms.length > 0 && <p className="topic-alert" role="status">Model structures unavailable · 模型缺少映射结构：{missingTerms.map(item => `${item.name.en} / ${item.name.zh}`).join('、')}</p>}
        </section>
        <aside className="study-panel topic-terms"><span className="eyebrow">EXPLORE · 结构浏览</span><h2>{term?.name.en}</h2>{showChinese && <p className="term-translation">{term?.name.zh}</p>}
          <label className="field-label" htmlFor="topic-term">Structure · 解剖结构</label>
          <select id="topic-term" value={termId} onChange={event => { const next = topic.viewer.terms.find(item => item.id === event.target.value); if (next) selectTerm(next); }}>
            {topic.viewer.terms.map(item => <option key={item.id} value={item.id} disabled={!availableTerms.includes(item)}>{item.name.en} · {item.name.zh}</option>)}
          </select>
          <div className="topic-term-list">{topic.viewer.terms.map(item => <button key={item.id} disabled={!availableTerms.includes(item)} aria-pressed={termId === item.id} onClick={() => selectTerm(item)}><strong>{item.name.en}</strong><span>{showChinese ? item.name.zh : item.kind === 'bone' ? 'Bone' : 'Muscle'}</span></button>)}</div>
          {reviewedLandmarks.length > 0 && <section className="bone-feature-list"><h3>Bone landmarks · 骨性标志</h3><div>{reviewedLandmarks.map(item => <button key={item.id} aria-pressed={landmarkId === item.id} disabled={!availableTerms.some(candidate => termStructures.get(candidate.id)?.has(item.structures[side]))} onClick={() => selectLandmark(item)}><span>{item.name.en}</span>{showChinese && <small>{item.name.zh}</small>}</button>)}</div></section>}
          {pendingLandmarkCount > 0 && <p className="muted">{pendingLandmarkCount} landmark positions await review. · {pendingLandmarkCount} 个骨性标志的位置待核对，尚未显示。</p>}
          <p>{topic.summary.en}</p><p className="muted">{topic.summary.zh}</p>
          {linkedTerm && !topic.viewer.terms.some(item => item.id === linkedTerm) && <p className="topic-alert" role="status">The linked term is unavailable; showing this topic’s default structure. · 链接中的词条未配置，现显示本主题默认结构。</p>}
        </aside>
      </main>}
    <footer><span>Models · 模型：<a href="https://github.com/vixotic/Vanatome" target="_blank" rel="noreferrer">Vanatome</a> · Z-Anatomy / BodyParts3D · <a href="./licenses/ASSET-LICENSE.md">CC BY-SA 4.0</a></span><a href="./study.html">Topic library · 主题目录</a></footer>
  </div>;
}

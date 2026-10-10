import { useEffect, useMemo, useRef, useState } from 'react';
import { VanatomeViewer } from './vendor/VanatomeViewer';
import type { VanatomeAnnotation, VanatomeCameraRequest, VanatomeAtlas, VanatomeDisplayMode, VanatomeSurfacePickEvent, VanatomeVector3 } from './vendor/types';
import { anatomyLabel, anatomyNames, anatomyEnglish, relatedEnglish, loadAtlases, modelPosition, modelScale, modelVersion, points, storageKey, validatePlacements, muscleGroups, initialMuscleGroups, muscleGroupOf, modelGroupOf } from './data';
import type { MuscleGroupId, Placement, Placements, PointKind } from './data';
import { modelReferences, referenceVersion } from './references';
import { VocabularyCard } from './VocabularyCard';
import { vocabularyById, termForAnatomy, pointRelatedTerms } from './vocabulary';
import { boneFocus, landmarkById, landmarksForBone, type BoneName } from './landmarks';
import { depthProbe, loadAcupointDepth, type DepthData } from './depth';
import { DepthSection } from './DepthPanel';
import { fitDockedLabels, useElementHeight } from './labelDock';

type Side = 'right' | 'left';
type View = 'back' | 'front' | 'side' | 'body';
type CameraIntent = VanatomeCameraRequest extends infer R ? R extends VanatomeCameraRequest ? Omit<R, 'id'> : never : never;
const initialCameraPosition: VanatomeVector3 = [-0.98, 3.65, -3.6];
const initialCameraTarget: VanatomeVector3 = [-0.98, 3.37, -0.34];
const kindNames: Record<PointKind, string> = { unconfirmed: '待核对的空间点', 'surface-reference': '体表定位参考', 'deep-reference': '深部解剖关联点' };
// Rotator cuff and the three bones keep their original fixed label slots (deltoid takes slot 7 when selected).
const legacyDockOrder = Object.keys(anatomyNames).filter(id => muscleGroupOf(id) === 'cuff' || id.startsWith('appendicular-skeleton-'));
// The 14 shoulder add-on muscles, by layer-bar group (EXPLORE strip and label priority).
const addonMuscleTerms = ['trapezius', 'latissimus-dorsi', 'levator-scapulae', 'rhomboid-major', 'rhomboid-minor', 'pectoralis-major', 'pectoralis-minor', 'subclavius', 'serratus-anterior', 'teres-major', 'biceps-brachii', 'triceps-brachii', 'coracobrachialis', 'brachialis'].filter(id => vocabularyById[id]);
// Multi-part add-on muscles carry one label (their own word) unless one of their parts is selected.
const labelledAsWhole = ['trapezius-muscles', 'pectoralis-major-muscles', 'biceps-brachii-muscles', 'triceps-brachii-muscles'];
const anteriorMuscles = ['pectoralis-major-muscles', 'pectoralis-minor-muscles', 'subclavius-muscles', 'biceps-brachii-muscles', 'coracobrachialis-muscles', 'brachialis-muscles'];
const lateralMuscles = ['serratus-anterior-muscles'];
const addonOrder = muscleGroups.filter(group => !group.initial).flatMap(group => group.groupIds);
const baseId = (id: string) => id.replace(/-(right|left)$/, '');
const toAnnotationSpace = (position: readonly number[]) => position.map((v, axis) => (v - modelPosition[axis]) / modelScale) as unknown as VanatomeVector3;

type LabelCandidate = { annotation: VanatomeAnnotation; base: string; priority: number; y: number; addon: boolean };
/** Anatomy-mode labels: legacy slots for the cuff + bones; otherwise a gap-free column, top to bottom by height,
 * keeping the highest-priority labels that fit the scene without overlapping. */
function layoutAnatomyLabels(candidates: LabelCandidate[], sceneHeight: number): { items: VanatomeAnnotation[]; total: number } {
  if (!candidates.some(item => item.addon)) {
    const slot = (item: LabelCandidate) => item.base.startsWith('deltoid') ? 7 : legacyDockOrder.indexOf(item.base);
    if (legacyDockOrder.every(id => candidates.some(item => item.base === id))) {
      return { items: candidates.map(item => ({ ...item.annotation, labelDockIndex: slot(item), labelDockCount: 8 })), total: candidates.length };
    }
    const order = [...candidates].sort((a, b) => slot(a) - slot(b));
    return { items: candidates.map(item => ({ ...item.annotation, labelDockIndex: order.indexOf(item), labelDockCount: candidates.length })), total: candidates.length };
  }
  return { items: fitDockedLabels(candidates, sceneHeight), total: candidates.length };
}
const whoUrl = 'https://iris.who.int/bitstream/handle/10665/353407/9789290613831-eng.pdf';

export default function App() {
  const [atlases, setAtlases] = useState<VanatomeAtlas[]>([]);
  const [error, setError] = useState('');
  const [ready, setReady] = useState(false);
  const [side, setSide] = useState<Side>('right');
  const [view, setView] = useState<View>('back');
  const [cameraRequest, setCameraRequest] = useState<VanatomeCameraRequest | null>(null);
  const cameraRequestId = useRef(0);
  const [freeRotation, setFreeRotation] = useState(false);
  const [displayMode, setDisplayMode] = useState<VanatomeDisplayMode>('xray');
  const [bones, setBones] = useState(true);
  const [muscles, setMuscles] = useState(true);
  const [groups, setGroups] = useState<Record<MuscleGroupId, boolean>>(initialMuscleGroups);
  const sceneRef = useRef<HTMLDivElement>(null);
  const sceneHeight = useElementHeight(sceneRef);
  // Only the selected structure, landmark or point is labelled until All labels is ticked (gui, 2026-10-09);
  // a bone view with no landmark chosen yet labels all of that bone's landmarks.
  const [allLabels, setAllLabels] = useState(false);
  const [showGuides, setShowGuides] = useState(false);
  const [showProbe, setShowProbe] = useState(true);
  const [depthData, setDepthData] = useState<DepthData | null>(null);
  const [depthError, setDepthError] = useState('');
  const [labelMode, setLabelMode] = useState<'anatomy' | 'landmarks' | 'acupoints'>('anatomy');
  const [detailBone, setDetailBone] = useState<BoneName>('humerus');
  const [landmarkId, setLandmarkId] = useState<string | null>(null);
  const [isolateBone, setIsolateBone] = useState(true);
  const [wholeBone, setWholeBone] = useState(false);
  const [showChinese, setShowChinese] = useState(true);
  const [termId, setTermId] = useState('infraspinatus');
  const [pointId, setPointId] = useState<string>('SI11');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [placements, setPlacements] = useState<Placements>({});
  const [storageReady, setStorageReady] = useState(false);
  const [autoSaveEnabled, setAutoSaveEnabled] = useState(true);
  const [notice, setNotice] = useState('');
  const [draft, setDraft] = useState('');
  const [showData, setShowData] = useState(false);
  const undoRef = useRef<Placements | null>(null);
  const linkedPointHandled = useRef(false);
  const point = points.find(p => p.id === pointId)!;
  const key = `${pointId}-${side}`;
  const effectivePlacements = useMemo(() => ({ ...modelReferences, ...placements }), [placements]);
  const placement = effectivePlacements[key];
  const reference = modelReferences[key];
  const customized = Boolean(placements[key]);
  const structures = useMemo(() => atlases.flatMap(a => a.structures), [atlases]);
  const boneDetail = labelMode === 'landmarks';
  const activeLandmark = landmarkId ? landmarkById[landmarkId] : undefined;
  const currentBoneLandmarks = landmarksForBone(detailBone);

  useEffect(() => { loadAtlases(['shoulder']).then(setAtlases).catch(e => setError(e instanceof Error ? e.message : String(e))); }, []);
  useEffect(() => { loadAcupointDepth().then(setDepthData).catch(e => setDepthError(e instanceof Error ? e.message : String(e))); }, []);
  useEffect(() => {
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) {
        const data = JSON.parse(raw);
        if (data.modelVersion !== modelVersion) throw new Error('模型版本不一致，未自动载入旧坐标');
        setPlacements(validatePlacements(data.placements));
      }
    } catch (e) { setAutoSaveEnabled(false); setNotice(`保存数据未载入：${e instanceof Error ? e.message : e}。原记录已保留。`); }
    setStorageReady(true);
  }, []);
  useEffect(() => {
    if (!storageReady || !autoSaveEnabled) return;
    try { localStorage.setItem(storageKey, JSON.stringify({ schemaVersion: 1, modelVersion, placements })); }
    catch { setNotice('浏览器无法保存；请用「导出坐标」保留本次标记。'); }
  }, [placements, storageReady, autoSaveEnabled]);
  useEffect(() => {
    if (!ready || !storageReady || linkedPointHandled.current) return;
    linkedPointHandled.current = true;
    if (cameraRequestId.current > 0) return;
    const linkedId = new URLSearchParams(location.search).get('point');
    const linkedTerm = new URLSearchParams(location.search).get('term');
    if (linkedTerm && vocabularyById[linkedTerm]) chooseTerm(linkedTerm);
    else if (linkedTerm && landmarkById[linkedTerm]) chooseLandmark(linkedTerm);
    else if (linkedId && points.some(p => p.id === linkedId)) choosePoint(linkedId, true);
  }, [ready, storageReady]);

  const depthEntry = depthData?.points[key];
  // With the depth probe on, every muscle the probe passes through stays visible, even when its group is off.
  const probeMuscleIds = useMemo(() => new Set(labelMode === 'acupoints' && showProbe && depthEntry
    ? depthEntry.layers.filter(layer => layer.kind === 'muscle').map(layer => layer.anatomyId) : []), [labelMode, showProbe, depthEntry]);
  const hiddenIds = useMemo(() => structures.filter(s => {
    if (!s.objectCount) return false;
    if (s.layer === 'skeletal') return !bones || (boneDetail && isolateBone ? s.id !== `appendicular-skeleton-${detailBone}-${side}` : view !== 'body' && !['scapula', 'clavicle', 'humerus'].some(n => s.id === `appendicular-skeleton-${n}-${side}`));
    if (s.layer === 'muscular') {
      if (!muscles || !s.id.endsWith(`-${side}`)) return true;
      if (probeMuscleIds.has(s.id)) return false;
      const group = muscleGroupOf(s.id);
      return !group || !groups[group];
    }
    return true;
  }).map(s => s.id), [structures, side, bones, muscles, groups, probeMuscleIds, view, boneDetail, isolateBone, detailBone]);
  const anatomyLabels = useMemo(() => {
    if (labelMode !== 'anatomy') return { items: [], total: 0 };
    const hidden = new Set(hiddenIds);
    // What was chosen: the selected structure or, with none selected (e.g. a ?point= link), the current word's structure.
    const termAnatomy = vocabularyById[termId]?.anatomy;
    const chosenId = selectedId ?? (termAnatomy ? (termAnatomy.endsWith('-muscles') ? termAnatomy : `${termAnatomy}-${side}`) : null);
    // Deltoid parts are labelled only when selected, or when they are the chosen word's structure while All labels is off.
    const deltoidLabelled = (id: string) => id === selectedId || selectedId === 'deltoid-muscles' || (!allLabels && (id === chosenId || chosenId === 'deltoid-muscles'));
    const visible = structures.filter(s => !hidden.has(s.id) && s.id.endsWith(`-${side}`) && anatomyEnglish[baseId(s.id)] && (!s.id.startsWith('deltoid') || deltoidLabelled(s.id)));
    const selectedWhole = selectedId && visible.some(s => s.id === selectedId) ? labelledAsWhole.find(group => selectedId.startsWith(group + '-')) : undefined;
    const candidates: LabelCandidate[] = [];
    const rank = (base: string, selected: boolean) => {
      const group = modelGroupOf(base) || '';
      if (selected) return 0;
      if (muscleGroupOf(base) === 'cuff') return 100 + legacyDockOrder.indexOf(base);
      return addonOrder.includes(group) ? 200 + addonOrder.indexOf(group) : 300 + legacyDockOrder.indexOf(base);
    };
    for (const s of visible) {
      const base = baseId(s.id);
      const whole = labelledAsWhole.find(group => base.startsWith(group + '-'));
      const addon = Boolean(modelGroupOf(base) && addonOrder.includes(modelGroupOf(base)!));
      if (whole && whole !== selectedWhole) {
        // One label for the whole muscle, at the middle of its visible parts on this side.
        if (candidates.some(item => item.base === whole)) continue;
        const parts = visible.filter(part => part.id.startsWith(whole + '-'));
        const centre = [0, 1, 2].map(axis => parts.reduce((sum, part) => sum + part.position[axis], 0) / parts.length);
        const term = termForAnatomy(whole);
        const name = `${side === 'right' ? 'Right · ' : 'Left · '}${term?.english || anatomyEnglish[base]}${showChinese ? `\n${term?.chinese || anatomyNames[base]}` : ''}`;
        candidates.push({ annotation: { id: `structure:${whole}`, label: name, position: toAnnotationSpace(centre), color: '#a6cbb9', showLabel: allLabels }, base: whole, priority: rank(whole, selectedId === whole), y: centre[1], addon });
        continue;
      }
      if (whole && s.id !== selectedId) continue;
      candidates.push({ annotation: { id: `structure:${s.id}`, label: anatomyLabel(s.id, showChinese).replace('Deltoid · ', ''), position: toAnnotationSpace(s.position), color: s.layer === 'skeletal' ? '#dfd2ad' : '#a6cbb9', showLabel: allLabels }, base, priority: rank(base, s.id === selectedId), y: s.position[1], addon });
    }
    if (!allLabels) {
      // Only what was chosen (chosenId above), or every part of a chosen muscle group.
      const group = chosenId?.endsWith('-muscles') ? chosenId + '-' : null;
      const chosen = candidates.filter(item => item.annotation.id === `structure:${chosenId}` || (group && (item.base === chosenId || item.base.startsWith(group))))
        .map(item => ({ ...item, annotation: { ...item.annotation, showLabel: true } }));
      return { items: fitDockedLabels(chosen, sceneHeight), total: chosen.length };
    }
    return layoutAnatomyLabels(candidates, sceneHeight);
  }, [labelMode, hiddenIds, structures, side, selectedId, showChinese, allLabels, sceneHeight, termId]);
  const annotations = useMemo(() => {
    if (labelMode === 'landmarks') {
      const items = landmarksForBone(detailBone);
      // A bone link (?term=humerus, Bone landmarks) is about its landmarks, so all of them are labelled until one is chosen.
      const labelAll = allLabels || !landmarkId;
      return bones ? items.map((item, i): VanatomeAnnotation => ({ id: `landmark:${item.id}`, label: `${item.english}${showChinese ? `\n${item.chinese}` : ''}`, position: item.positions[side], color: item.id === landmarkId ? '#f1c16f' : '#b6cfbd', showLabel: labelAll, labelDockIndex: labelAll ? i : 0, labelDockCount: labelAll ? items.length : 1 })) : [];
    }
    if (labelMode === 'anatomy') {
      const items = [...anatomyLabels.items];
      if (termId === 'posterior-shoulder') items.push({ id: 'region:posterior-shoulder', label: `Posterior shoulder · region${showChinese ? '\n肩后区 · 区域参照' : ''}`, position: modelReferences[`SI9-${side}`].position, color: '#e6b96b', showLabel: true });
      return items;
    }
    const items: VanatomeAnnotation[] = points.flatMap(p => {
    const id = `${p.id}-${side}`;
    const saved = effectivePlacements[id];
    const original = modelReferences[id];
    const isReference = !placements[id];
    return saved ? [{ id, label: `${p.english} · ${p.id}${showChinese ? ` ${p.name}` : ''}\n${isReference ? 'Study reference' : 'Custom'}`, position: saved.position, color: p.color, showLabel: allLabels, labelDockIndex: allLabels ? ['SI12','LI15','TE14','SI9','SI11'].indexOf(p.id) : undefined, labelDockCount: 5, guidePath: showGuides && id === key && isReference ? original?.guidePath : undefined, guideLabels: showGuides && id === key && isReference ? original?.guideLabels?.map(g => { const [cn, en] = g.label.split(' · '); return { ...g, label: en ? `${en}${showChinese ? ` · ${cn}` : ''}` : g.label }; }) : undefined }] : [];
    });
    const structure = structures.find(s => s.id === selectedId);
    if (structure && anatomyEnglish[structure.id.replace(/-(right|left)$/, '')]) {
      items.push({ id: `structure:${structure.id}`, label: anatomyLabel(structure.id, showChinese), position: structure.position.map((v, i) => (v - modelPosition[i]) / modelScale) as unknown as VanatomeVector3, color: '#d2e0d3' });
    }
    return items;
  }, [effectivePlacements, placements, side, key, allLabels, showGuides, selectedId, structures, labelMode, showChinese, anatomyLabels, detailBone, landmarkId, bones, termId]);
  const detailTarget = activeLandmark?.positions[side] || boneFocus(detailBone, side);
  // The depth probe follows the built-in reference of the selected point (Acupoints mode only).
  const probes = useMemo(() => labelMode === 'acupoints' && showProbe && depthEntry ? [depthProbe(depthEntry, point.color, showChinese, customized)] : [], [labelMode, showProbe, depthEntry, point.color, showChinese, customized]);

  function requestCamera(intent: CameraIntent) {
    setCameraRequest({ ...intent, id: ++cameraRequestId.current } as VanatomeCameraRequest);
  }
  function directionFor(nextView: View, nextSide = side): VanatomeVector3 {
    return nextView === 'side' ? [nextSide === 'right' ? -1 : 1, 0.14, 0.08] : [nextSide === 'right' ? 0.2 : -0.2, 0.14, nextView === 'front' ? 1 : -1];
  }
  function shoulderCenter(nextSide = side): VanatomeVector3 {
    return [nextSide === 'right' ? -0.14 : 0.14, (3.37 - modelPosition[1]) / modelScale, -0.34 / modelScale];
  }
  function boneDistance(bone: BoneName, feature?: string) {
    return bone === 'humerus' ? 1.3 : feature && ['acromion', 'anterolateral-acromion', 'posterolateral-acromion'].includes(feature) ? 1.25 : 2.6;
  }
  function moveView(next: View) {
    setView(next); setFreeRotation(false); setEditing(false);
    if (next === 'body') {
      setLabelMode('anatomy'); setSelectedId(null); setBones(true);
      requestCamera({ kind: 'structure', structureId: 'skeletal-system', direction: [0, 0.06, -1], distance: 12 });
    } else if (view === 'body') {
      requestCamera({ kind: 'point', target: shoulderCenter(), direction: directionFor(next), distance: 3.3 });
    } else {
      // A view button changes only the orbit, keeping the current focus/zoom.
      requestCamera({ kind: 'orbit', direction: directionFor(next) });
    }
  }
  function changeSide(nextSide: Side) {
    if (nextSide === side) return;
    setSide(nextSide); setEditing(false);
    if (view === 'body') return;
    const direction = view === 'side' && !freeRotation ? directionFor('side', nextSide) : undefined;
    if (boneDetail) {
      const id = `appendicular-skeleton-${detailBone}-${nextSide}`;
      setSelectedId(id);
      if (wholeBone) requestCamera({ kind: 'structure', structureId: id, direction, distance: 2.5 });
      else requestCamera({ kind: 'point', target: activeLandmark?.positions[nextSide] || boneFocus(detailBone, nextSide), direction, preserveDistance: true });
    } else if (labelMode === 'acupoints') {
      setSelectedId(null);
      requestCamera({ kind: 'point', target: effectivePlacements[`${pointId}-${nextSide}`].position, direction, preserveDistance: true });
    } else if (selectedId) {
      const id = selectedId.replace(/-(right|left)$/, `-${nextSide}`);
      setSelectedId(id);
      requestCamera({ kind: 'structure', structureId: id, direction });
    } else requestCamera({ kind: 'point', target: shoulderCenter(nextSide), direction, preserveDistance: true });
  }
  function choosePoint(id: string, initial = false) {
    const p = points.find(p => p.id === id)!;
    const keepView = labelMode === 'acupoints' && view !== 'body';
    const nextView = id === 'LI15' ? 'front' : 'back';
    setPointId(id); setEditing(false);
    setTermId(initial ? (termForAnatomy(p.anatomy)?.id || 'infraspinatus') : id.toLowerCase());
    if (!initial) setLabelMode('acupoints');
    setMuscles(true); setBones(true); showMuscleGroup(p.anatomy);
    if (!keepView) { setView(nextView); setFreeRotation(false); }
    const saved = effectivePlacements[`${id}-${side}`];
    const direction = keepView ? undefined : directionFor(nextView);
    if (saved) {
      setSelectedId(null);
      requestCamera({ kind: 'point', target: saved.position, direction, distance: 2.5, preserveDistance: keepView });
    } else {
      const anatomyId = `${p.anatomy}-${side}`;
      setSelectedId(anatomyId);
      requestCamera({ kind: 'structure', structureId: anatomyId, direction });
    }
  }
  function selectStructure(id: string | null) {
    if (!id) { if (!boneDetail) setSelectedId(null); return; }
    const bone = id.replace(/-(right|left)$/, '').replace('appendicular-skeleton-', '');
    const selectedSide = id.endsWith('-left') ? 'left' : id.endsWith('-right') ? 'right' : side;
    if (bone === 'humerus' || bone === 'scapula') { chooseBone(bone, selectedSide); return; }
    // Keep other skeleton structures visible while focusing them from the body view.
    if (view === 'body' && !termForAnatomy(id)) {
      setSelectedId(id);
      requestCamera({ kind: 'structure', structureId: id });
      return;
    }
    setSide(selectedSide); setSelectedId(id); setLabelMode('anatomy'); showMuscleGroup(id);
    if (view === 'body') setView('back');
    const term = termForAnatomy(id);
    if (term) setTermId(term.id);
    requestCamera({ kind: 'structure', structureId: id });
  }
  function chooseTerm(id: string) {
    const term = vocabularyById[id];
    if (!term) return;
    if (term.pointId) { choosePoint(term.pointId); return; }
    if (landmarkById[id]) { chooseLandmark(id); return; }
    if (id === 'humerus' || id === 'scapula') { chooseBone(id); return; }
    const preserveView = freeRotation && view !== 'body';
    const muscle = term.anatomy ? modelGroupOf(term.anatomy) : undefined;
    const nextView: View = ['subscapularis', 'clavicle', 'clavicular-part'].includes(id) || (muscle && anteriorMuscles.includes(muscle)) ? 'front'
      : muscle && lateralMuscles.includes(muscle) ? 'side' : 'back';
    setTermId(id); setLabelMode('anatomy'); setEditing(false); setBones(true); setMuscles(true);
    if (!preserveView) { setView(nextView); setFreeRotation(false); }
    if (term.anatomy) {
      showMuscleGroup(term.anatomy);
      // A whole-muscle word (rotator cuff, trapezius…) selects its model group; only this side is visible, so only this side is framed.
      const anatomyId = term.anatomy.endsWith('-muscles') ? term.anatomy : `${term.anatomy}-${side}`;
      setSelectedId(anatomyId);
      requestCamera({ kind: 'structure', structureId: anatomyId, direction: preserveView ? undefined : directionFor(nextView) });
    }
  }
  function showMuscleGroup(anatomyId: string) {
    const group = muscleGroupOf(anatomyId);
    if (group) setGroups(current => current[group] ? current : { ...current, [group]: true });
  }
  function toggleMuscleGroup(group: MuscleGroupId, on: boolean) {
    setGroups(current => ({ ...current, [group]: on }));
    if (on) setMuscles(true);
    else if (selectedId && muscleGroupOf(selectedId) === group) setSelectedId(null);
  }
  function muscleGroupBox(group: (typeof muscleGroups)[number]) {
    return <label key={group.id} className={muscles ? undefined : 'muscles-hidden'}><input type="checkbox" checked={groups[group.id]} onChange={e => toggleMuscleGroup(group.id, e.target.checked)} />{group.en} · {group.zh}</label>;
  }
  function chooseBone(bone: BoneName, nextSide = side) {
    const sameBone = boneDetail && detailBone === bone && nextSide === side && !wholeBone;
    setSide(nextSide); setDetailBone(bone); setLandmarkId(null); setLabelMode('landmarks'); setWholeBone(false);
    setTermId(bone); setBones(true); setMuscles(false); setEditing(false);
    const nextView = bone === 'humerus' ? 'front' : 'back';
    if (!sameBone) { setView(nextView); setFreeRotation(false); }
    setSelectedId(`appendicular-skeleton-${bone}-${nextSide}`);
    requestCamera({ kind: 'point', target: boneFocus(bone, nextSide), direction: sameBone ? undefined : directionFor(nextView, nextSide), distance: boneDistance(bone), preserveDistance: sameBone });
  }
  function chooseLandmark(id: string) {
    const item = landmarkById[id];
    if (!item) return;
    const bone = item.anatomy.endsWith('humerus') ? 'humerus' : 'scapula';
    const sameBone = boneDetail && detailBone === bone;
    setDetailBone(bone); setLandmarkId(id); setLabelMode('landmarks'); setWholeBone(false);
    setTermId(vocabularyById[id] ? id : bone); setBones(true); setMuscles(false); setEditing(false);
    if (!sameBone) { setView(item.view); setFreeRotation(false); }
    setSelectedId(`${item.anatomy}-${side}`);
    requestCamera({ kind: 'point', target: item.positions[side], direction: sameBone ? undefined : directionFor(item.view), distance: boneDistance(bone, id), preserveDistance: sameBone && !wholeBone });
  }
  function toggleWholeBone() {
    setWholeBone(v => !v);
    if (wholeBone) requestCamera({ kind: 'point', target: detailTarget, distance: boneDistance(detailBone, landmarkId || undefined) });
    else requestCamera({ kind: 'structure', structureId: `appendicular-skeleton-${detailBone}-${side}`, distance: 2.5 });
  }
  function switchLabels(mode: 'anatomy' | 'landmarks' | 'acupoints') {
    if (mode === labelMode) return;
    if (mode === 'landmarks') { chooseBone(detailBone); return; }
    if (mode === 'acupoints') { choosePoint(pointId); return; }
    setLabelMode('anatomy'); setSelectedId(null); setBones(true); setMuscles(true); setLandmarkId(null);
    if (view === 'body') { setView('back'); setFreeRotation(false); }
    requestCamera({ kind: 'point', target: shoulderCenter(), distance: 3.3, direction: view === 'body' ? directionFor('back') : undefined });
  }
  function pick(event: VanatomeSurfacePickEvent) {
    if (!editing) return;
    if (!Object.keys(anatomyNames).some(id => event.id === `${id}-${side}`)) {
      setNotice(`请选取${side === 'right' ? '右' : '左'}肩的骨骼或肌肉；另一侧与其他部位不会写入此标记。`);
      return;
    }
    undoRef.current = placements;
    setPlacements(p => ({ ...p, [key]: { position: [...event.position], anatomyId: event.id, kind: 'unconfirmed', note: p[key]?.note || '' } }));
    setSelectedId(null); setEditing(false);
    setNotice('已记录选中结构上的起点；可沿三个轴调整至需要观察的空间位置。');
  }
  function updatePlacement(patch: Partial<Placement>) {
    if (!placement) return;
    undoRef.current = placements;
    setPlacements(p => ({ ...p, [key]: { position: [...placement.position], anatomyId: placement.anatomyId, kind: placement.kind, note: placement.note, ...patch } }));
  }
  function coordinate(axis: number, value: number) {
    if (!placement || !Number.isFinite(value)) return;
    const position: [number, number, number] = [...placement.position];
    const lower = axis === 1 || (axis === 0 && side === 'left') ? 0 : -0.7;
    const upper = axis === 1 ? 2 : axis === 0 && side === 'right' ? 0 : 0.7;
    position[axis] = Math.max(lower, Math.min(upper, value));
    updatePlacement({ position });
    if (labelMode === 'acupoints') requestCamera({ kind: 'point', target: position, preserveDistance: true });
  }
  function exportData() {
    const text = JSON.stringify({ schemaVersion: 1, modelVersion, referenceVersion, coordinateSystem: 'original-model-metres-y-up', interpretation: '深部解剖学习参照；非临床穴位中心。Deep anatomical study references, not clinically localized acupoint centers.', placements: effectivePlacements }, null, 2);
    setDraft(text); setShowData(true);
    const url = URL.createObjectURL(new Blob([text], { type: 'application/json' }));
    const a = document.createElement('a'); a.href = url; a.download = '肩部空间标记.json'; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    setNotice('已导出坐标；下方也保留可复制的数据。');
  }
  function importData() {
    try {
      const data = JSON.parse(draft);
      if (data.schemaVersion !== 1 || data.modelVersion !== modelVersion) throw new Error('数据版本或人体模型不匹配');
      const imported = validatePlacements(data.placements);
      undoRef.current = placements; setPlacements(p => ({ ...p, ...imported }));
      setNotice(`已合并 ${Object.keys(imported).length} 个标记，可撤销本次操作。`);
    } catch (e) { setNotice(`未导入：${e instanceof Error ? e.message : e}`); }
  }
  function restoreLast() {
    if (!undoRef.current) return;
    const prior = undoRef.current; undoRef.current = placements; setPlacements(prior); setNotice('已撤销上一步坐标修改。');
  }

  return <div className="app">
    <header className="masthead"><div><span className="eyebrow">SHOULDER · SPATIAL STUDY</span><h1>Shoulder anatomy<span>肩部三维 · 英语学习</span></h1></div><a className="reading-link" href="./reading.html" target="_blank" rel="noreferrer">Reading notes · 阅读笔记 ↗</a></header>
    <main className="workspace">
      <section className="viewer-panel" aria-label="三维人体工作区">
        <div className="toolbar has-end"><div className="segments side-switch">{(['right', 'left'] as const).map(s => <button key={s} aria-pressed={side === s} onClick={() => changeSide(s)}>{s === 'right' ? 'Right · 右肩' : 'Left · 左肩'}</button>)}</div><div className="toolbar-end"><div className="segments">{([['back', 'Posterior'], ['front', 'Anterior'], ['side', 'Lateral'], ['body', 'Skeleton']] as const).map(([v, label]) => <button key={v} aria-pressed={view === v && !freeRotation} onClick={() => moveView(v)}>{label}</button>)}</div><div className="segments muscle-switch"><button className={muscles ? undefined : 'active'} onClick={() => setMuscles(shown => !shown)}>{muscles ? 'Hide muscles · 隐藏肌肉' : 'Show muscles · 显示肌肉'}</button></div></div></div>
        <div className="bone-view-slot"><div className="bone-view-controls" style={{visibility: boneDetail ? 'visible' : 'hidden'}} aria-hidden={!boneDetail}><div className="segments"><button aria-pressed={detailBone === 'humerus'} onClick={() => chooseBone('humerus')}>Humerus</button><button aria-pressed={detailBone === 'scapula'} onClick={() => chooseBone('scapula')}>Scapula</button></div><label><input type="checkbox" checked={isolateBone} onChange={e => setIsolateBone(e.target.checked)} />Isolate bone · 单骨</label><button aria-pressed={wholeBone} onClick={toggleWholeBone}>{wholeBone ? 'Close-up · 局部' : 'Whole bone · 全骨'}</button></div></div>
        <div ref={sceneRef} className={`scene ${editing ? 'editing' : ''}`}>
          {atlases.length > 0 && !error && <VanatomeViewer atlases={atlases} modelScale={modelScale} modelPosition={modelPosition} initialCameraPosition={initialCameraPosition} initialCameraTarget={initialCameraTarget} cameraRequest={cameraRequest} enablePan minDistance={0.7} maxDistance={28} focusDistance={2.5} hiddenIds={hiddenIds} selectedId={selectedId} displayMode={displayMode} annotations={annotations} probes={probes} selectedAnnotationId={boneDetail ? landmarkId ? `landmark:${landmarkId}` : null : termId === 'posterior-shoulder' ? 'region:posterior-shoulder' : selectedId ? `structure:${selectedId}` : key} annotationEditing={editing} onSurfacePick={pick} onAnnotationSelect={id => { if (id.startsWith('landmark:')) chooseLandmark(id.slice(9)); else if (id.startsWith('region:')) chooseTerm(id.slice(7)); else if (id.startsWith('structure:')) selectStructure(id.slice(10)); else choosePoint(id.replace(/-(right|left)$/, '')); }} onSelect={selectStructure} onReady={() => setReady(true)} onError={e => setError(e.message)} onEscape={() => setEditing(false)} onInteractionStart={() => setFreeRotation(true)} appearance={{ xrayOpacity: 0.32, ghostOpacity: 0.13, pulseSelection: false, skeletonId: 'skeletal-system', bodyShellId: null }} loadingFallback={<div className="loading">正在载入真实解剖模型…</div>} ariaLabel="可旋转的肩部三维解剖模型" />}
          {error && <div className="loading error">模型未能载入：{error}<button onClick={() => location.reload()}>重新载入</button></div>}
          <div className="scene-caption"><span className="live-dot" />{editing ? `Select a starting point · ${point.english}` : boneDetail ? `${activeLandmark?.english || (detailBone === 'humerus' ? 'Humerus · proximal end' : 'Scapula')} · Bone landmarks` : labelMode === 'anatomy' ? `Anatomy · ${vocabularyById[termId].english}` : `${point.english} ${point.id} · ${customized ? 'Custom' : 'Study reference'}`}</div>
          <div className="scene-help">Drag to rotate · Scroll to zoom</div>
          <div className={`orientation${anatomyLabels.items.filter(item => item.labelDockIndex !== undefined).length > 8 ? ' beside-dock' : ''}`}>{side === 'right' ? 'R' : 'L'}<small>{freeRotation ? 'Free view' : view === 'back' ? 'Posterior view' : view === 'front' ? 'Anterior view' : view === 'side' ? 'Lateral view' : 'Skeleton'}</small></div>
        </div>
        {labelMode === 'anatomy' && allLabels && anatomyLabels.items.length < anatomyLabels.total && <p className="label-note" role="status">{anatomyLabels.items.length} of {anatomyLabels.total} labels fit the view; select a muscle or turn off a group to see the rest. · 视图中可显示 {anatomyLabels.items.length}/{anatomyLabels.total} 个标注；点选肌肉或关闭部分肌群可查看其余名称。</p>}
        <div className="layerbar"><div className="segments">{([['normal', 'Solid'], ['xray', 'X-ray'], ['ghost', 'Ghost']] as const).map(([mode, label]) => <button key={mode} aria-pressed={displayMode === mode} onClick={() => setDisplayMode(mode)}>{label}</button>)}</div><label><input type="checkbox" checked={bones} onChange={e => setBones(e.target.checked)} />Bones · 骨骼</label>{muscleGroups.filter(group => group.initial).map(muscleGroupBox)}<div className="layer-more" role="group" aria-label="More muscles · 更多肌肉"><span className="layer-more-title">More muscles · 更多肌肉</span>{muscleGroups.filter(group => !group.initial).map(muscleGroupBox)}</div></div>
        <div className="annotation-options"><div className="segments"><button aria-pressed={labelMode === 'anatomy'} onClick={() => switchLabels('anatomy')}>Anatomy · 解剖</button><button aria-pressed={boneDetail} onClick={() => switchLabels('landmarks')}>Bone landmarks · 骨标</button><button aria-pressed={labelMode === 'acupoints'} onClick={() => switchLabels('acupoints')}>Acupoints · 穴位</button></div><label><input type="checkbox" checked={allLabels} onChange={e => setAllLabels(e.target.checked)} />All labels</label><label><input type="checkbox" checked={showGuides} onChange={e => { setShowGuides(e.target.checked); if (e.target.checked && labelMode !== 'acupoints') choosePoint(pointId); }} />Point guides</label><label><input type="checkbox" checked={showProbe} onChange={e => { setShowProbe(e.target.checked); if (e.target.checked && labelMode !== 'acupoints') choosePoint(pointId); }} />Depth probe · 深浅探针</label></div>
        <div className="anatomy-strip"><span>EXPLORE</span>{legacyDockOrder.map(id => <button key={id} aria-pressed={selectedId === `${id}-${side}`} onClick={() => { const term = termForAnatomy(id); if (term) chooseTerm(term.id); }}><span>{anatomyEnglish[id]}</span>{showChinese && <small>{anatomyNames[id]}</small>}</button>)}{addonMuscleTerms.map(id => { const term = vocabularyById[id]; const anatomy = term.anatomy || ''; const pressed = Boolean(selectedId) && (anatomy.endsWith('-muscles') ? selectedId === anatomy || (selectedId!.startsWith(anatomy + '-') && selectedId!.endsWith(`-${side}`)) : selectedId === `${anatomy}-${side}`); return <button key={id} className="addon-term" aria-pressed={pressed} onClick={() => chooseTerm(id)}><span>{term.english}</span>{showChinese && <small>{term.chinese}</small>}</button>; })}</div>
        <div className="reference-note"><strong>Learn the structure, then its name · 看结构，记英语</strong><p>点击 Humerus / Scapula 会展开骨性结构；点选骨标可看具体位置，Whole bone 切回整骨。骨面标记用于辨认结构所在区域。Acupoints 中的体内学习参照不表示统一的穴位中心。</p></div>
      </section>

      <aside className="study-panel">
        <VocabularyCard term={vocabularyById[termId]} showChinese={showChinese} onToggleChinese={() => setShowChinese(s => !s)} onChoose={chooseTerm} />
        {boneDetail ? <section className="bone-feature-list" aria-label="Bone landmarks"><span className="eyebrow">{detailBone === 'humerus' ? 'HUMERUS · PROXIMAL END' : 'SCAPULA · BONE LANDMARKS'}</span><div>{currentBoneLandmarks.map(item => <button key={item.id} aria-pressed={landmarkId === item.id} onClick={() => chooseLandmark(item.id)}><span>{item.english}</span>{showChinese && <small>{item.chinese}</small>}</button>)}</div>{activeLandmark && <p>{showChinese ? activeLandmark.description : activeLandmark.description.split(' / ')[0]}</p>}<details><summary>About these markers · 标记说明</summary><p>{activeLandmark?.basis || 'Dots identify representative positions on this model, not entire boundaries. 点标记本模型上的代表位置，不表示完整结构边界。'}</p><p>Humerus detail is limited by the original mesh. 肱骨原模型细节有限，沟与颈使用近似区域标记。</p><a href={currentBoneLandmarks[0]?.sourceURLs[0]} target="_blank" rel="noreferrer">Anatomy reference ↗</a></details></section> : <div className="related-words"><span className="eyebrow">RELATED TO {point.id}</span><div>{pointRelatedTerms[point.id].map(id => <button key={id} aria-pressed={termId === id} onClick={() => chooseTerm(id)}>{vocabularyById[id].english}</button>)}</div></div>}
        <div className="panel-heading"><span className="eyebrow">ACUPOINT NOTEBOOK</span><h2>Acupoint references</h2><p>穴位学习参照 · Pinyin names & international codes</p></div>
        <nav className="point-list" aria-label="Acupoints">{points.map(p => <button key={p.id} aria-pressed={pointId === p.id && labelMode === 'acupoints'} onClick={() => choosePoint(p.id)}><i style={{ background: p.color }} /><span>{p.english}<b>{p.id}</b>{showChinese && <small>{p.name}</small>}</span><em>{placements[`${p.id}-${side}`] ? 'Custom' : 'Study ref.'}</em></button>)}</nav>
        <article className="point-detail"><div className="detail-title"><h2>{point.english} <small>{point.id}</small>{showChinese && <em>{point.name}</em>}</h2><span>{side === 'right' ? 'Right 右' : 'Left 左'}</span></div><h3>Standard location · 标准定位参照</h3><p>{point.location}</p><p className="muted">{point.cue}</p><h3>Related anatomy · 相关解剖</h3><p>{relatedEnglish[point.id]}{showChinese && <span className="english-line">{point.related}</span>}</p><a className="source-link" href={whoUrl} target="_blank" rel="noreferrer">WHO 穴位定位标准 · 印刷页 {point.page} ↗</a><a className="source-link" href="https://www.medbox.org/index.php/dl/627a4de115110145a1723f64" target="_blank" rel="noreferrer">可读镜像 · PDF mirror ↗</a>
          <DepthSection entry={depthEntry} error={depthError} showChinese={showChinese} customized={customized} markerColor={point.color} />
          <div className="reference-evidence"><h3>Model reference · 模型参照</h3>{customized && <p className="tiny">下方是内置参照的依据，你的调整另行保存。</p>}<p className="reference-tissue">{anatomyLabel(reference.anatomyId, showChinese)}</p><p>{reference.method}</p><details><summary>Basis & limitations · 定位依据与模型差异</summary><p>{reference.limitation}</p><p className="tiny">骨性参考线用于解释位置关系；不表示进针路径。数值仅记录本模型坐标。</p><a href="./calibration-evidence.json" target="_blank" rel="noreferrer">查看模型核对记录 ↗</a></details></div><details className="edit-panel"><summary>Edit & notes · 调整位置 / 记录笔记</summary><div className="placement-box"><h3>三维位置 <span>{placement ? kindNames[placement.kind] : '尚未记录'}</span></h3>{!placement && <p className="muted">当前聚焦相关解剖结构。需要依据骨性标志校准后，才会出现对应标记。</p>}<button className={editing ? 'primary active' : 'primary'} disabled={!ready || !!error} onClick={() => { setEditing(e => !e); setNotice(''); }}>{editing ? '取消取点' : placement ? '重新选取空间起点' : '在模型中选取起点'}</button>
          {placement && <><label className="field-label" htmlFor="point-kind">标记含义</label><select id="point-kind" value={placement.kind} onChange={e => updatePlacement({ kind: e.target.value as PointKind })}>{Object.entries(kindNames).map(([v, n]) => <option key={v} value={v}>{n}</option>)}</select><p className="origin">起点结构：{anatomyLabel(placement.anatomyId, showChinese)}</p><div className="coordinates">{['X 左右', 'Y 上下', 'Z 前后'].map((label, i) => <label key={label}>{label}<div><button aria-label={`${label}减小`} onClick={() => coordinate(i, placement.position[i] - 0.001)}>−</button><input aria-label={`${label}坐标`} type="number" step="0.001" value={Number(placement.position[i].toFixed(4))} onChange={e => coordinate(i, e.target.valueAsNumber)} /><button aria-label={`${label}增大`} onClick={() => coordinate(i, placement.position[i] + 0.001)}>+</button></div></label>)}</div><p className="tiny">模型坐标，单位为米；每步 0.001。调整空间位置不等于确定穿刺深度。</p><label className="field-label" htmlFor="placement-note">定位依据 / 学习笔记</label><textarea id="placement-note" value={placement.note} maxLength={3000} placeholder="记录依据的骨性标志、层次和待核对的问题…" onChange={e => updatePlacement({ note: e.target.value })} /><div className="inline-actions"><button onClick={() => choosePoint(pointId)}>聚焦此标记</button><button disabled={!customized} onClick={() => { undoRef.current = placements; setPlacements(p => { const next = { ...p }; delete next[key]; return next; }); requestCamera({ kind: 'point', target: reference.position, preserveDistance: true }); setNotice('已恢复内置模型参照，可撤销。'); }}>恢复模型参照</button></div></>}
          </div></details>
        </article>
        <div className="data-actions"><button onClick={exportData}>导出坐标</button><button onClick={() => setShowData(s => !s)}>导入 / 查看数据</button><button disabled={!undoRef.current} onClick={restoreLast}>撤销</button></div><div className="status" role="status">{notice || '内置参照已载入；你的调整自动保存在此浏览器。'}{!autoSaveEnabled && <p>自动保存已暂停以保留原记录。请导出本次编辑。</p>}</div>
        {showData && <div className="json-panel"><label htmlFor="json-data">标记数据 JSON</label><textarea id="json-data" value={draft} onChange={e => setDraft(e.target.value)} placeholder="粘贴之前导出的坐标文件内容" /><button onClick={importData}>校验并合并标记</button></div>}
      </aside>
    </main>
    <footer><span>模型：<a href="https://github.com/vixotic/Vanatome" target="_blank" rel="noreferrer">Vanatome</a> · Z-Anatomy / BodyParts3D · <a href="./licenses/ASSET-LICENSE.md" target="_blank">CC BY-SA 4.0</a></span><span>本地学习版 · 解剖学习参照 · Anatomical study references</span></footer>
  </div>;
}

import type { CSSProperties, ReactElement } from 'react';
import { formatCm, structureColor } from './depth';
import type { DepthEntry, DepthSourceComparison, DepthText } from './depth';

const stopNotes: Record<string, DepthText> = {
  'thoracic-wall': { en: 'The list stops at the rib (thoracic wall).', zh: '列表到肋（胸壁）为止。' },
  humerus: { en: 'The list stops at the humerus.', zh: '列表到肱骨为止。' },
  'unmodeled-gap': { en: 'The list stops where no modeled structure follows within 1.5 cm.', zh: '其后 1.5 cm 内没有建模结构，列表到此为止。' },
  'no-further-structure': { en: 'No further modeled structure lies deeper on this axis.', zh: '此轴线更深处没有其他建模结构。' },
  'max-depth': { en: 'The list stops at 8 cm.', zh: '列表到 8 cm 为止。' },
};

type Props = {
  entry?: DepthEntry;
  error?: string;
  showChinese: boolean;
  customized: boolean;
  markerColor: string;
};

/** "Depth & surroundings" for one acupoint study reference (one side). */
export function DepthSection({ entry, error, showChinese, customized, markerColor }: Props) {
  const zh = (text?: string) => (showChinese && text ? text : '');
  const heading = <h3>Depth & surroundings · 深浅与周围结构</h3>;
  if (error) return <section className="depth-section" aria-label="Depth and surroundings">{heading}<p className="tiny">Depth data unavailable · 深浅数据未能载入：{error}</p></section>;
  if (!entry) return <section className="depth-section" aria-label="Depth and surroundings">{heading}<p className="tiny">Loading depth data… · 正在读取深浅数据…</p></section>;
  const { axis } = entry;
  const ownId = entry.referenceAnatomyId;
  const bone = axis.firstBoneSurface && entry.layers.find(layer => layer.anatomyId === axis.firstBoneSurface!.anatomyId);
  const stop = stopNotes[axis.layerStopReason];
  const range = axis.sensitivity.referenceDepthCm;
  const depthRange = formatCm(range.min) === formatCm(range.max) ? formatCm(range.min) : `${formatCm(range.min)}–${formatCm(range.max)}`;
  return <section className="depth-section" aria-label="Depth and surroundings">
    {heading}
    {customized && <p className="tiny depth-custom">These depths describe the built-in model reference, not your custom position.{showChinese && ' 以下深度对应内置模型参照，不是你的自定义位置。'}</p>}
    <p className="depth-axis"><span>Probe axis{zh(' · 探针轴线')}</span>{axis.approachLabel.en}{zh(axis.approachLabel.zh) && ` · ${axis.approachLabel.zh}`}, perpendicular to the modeled outer surface{zh(' · 垂直于模型外表面')}</p>
    <ol className="depth-strip">
      <li className="depth-row depth-skin">
        <span className="depth-bar" aria-hidden="true" />
        <div className="depth-body"><div className="depth-line"><b>Skin & subcutaneous tissue</b></div>{showChinese && <small className="depth-zh">皮肤与皮下组织</small>}<small className="depth-missing">Not in the model{zh(' · 模型未包含')}</small></div>
      </li>
      {entry.layers.flatMap((layer, i) => {
        const own = layer.anatomyId === ownId && layer.containsReference;
        const alsoReference = layer.containsReference && !own;
        const color = structureColor(layer.anatomyId, layer.kind);
        const height = Math.round(Math.min(98, Math.max(46, 30 + layer.thicknessCm * 16)));
        const referencePercent = Math.min(94, Math.max(6, (entry.referenceDepthCm - layer.entryCm) / Math.max(layer.thicknessCm, 0.01) * 100));
        const rows: ReactElement[] = [];
        if (i > 0 && layer.gapBeforeCm >= 0.1) rows.push(<li key={`${layer.anatomyId}-gap`} className="depth-row depth-gap"><span className="depth-bar" aria-hidden="true" /><div className="depth-body"><small>{formatCm(layer.gapBeforeCm)} cm without a modeled structure{zh(' · 无建模结构')}</small></div></li>);
        rows.push(<li key={layer.anatomyId} className={`depth-row depth-layer${own ? ' is-reference' : ''}`} style={{ '--layer': color, '--marker': markerColor, minHeight: height } as CSSProperties}>
          <span className="depth-bar" aria-hidden="true">{own && <i className="depth-ref-dot" style={{ top: `${referencePercent}%` }} />}</span>
          <div className="depth-body">
            <div className="depth-line"><b>{layer.english}</b><span className="depth-range">{formatCm(layer.entryCm)}–{formatCm(layer.exitCm)} cm</span></div>
            <div className="depth-line depth-sub">{showChinese && layer.chinese ? <small className="depth-zh">{layer.chinese}</small> : <span />}<small>{formatCm(layer.thicknessCm)} cm thick{zh(' · 厚')}</small></div>
            {own && <p className="depth-ref">● Reference{zh(' 参照点')} {formatCm(entry.referenceDepthCm)} cm</p>}
            {alsoReference && <small className="depth-note">The reference also lies inside this mesh (source meshes overlap).{zh(' 参照点也位于此网格内（原始网格重叠）。')}</small>}
            {layer.overlapsPreviousCm >= 0.05 && <small className="depth-note">Its mesh overlaps the layer above by {formatCm(layer.overlapsPreviousCm)} cm.{zh(` 与上一层网格重叠 ${formatCm(layer.overlapsPreviousCm)} cm。`)}</small>}
            {layer.note && <small className="depth-note">{layer.note.en}{zh(` ${layer.note.zh}`)}</small>}
          </div>
        </li>);
        return rows;
      })}
    </ol>
    {stop && <p className="tiny depth-stop">{stop.en}{zh(` ${stop.zh}`)}</p>}

    <h4 className="depth-subheading">Nearby structures · 周围结构 <small>within 3 cm of the reference{zh(' · 参照点 3 cm 内')}</small></h4>
    <ul className="depth-nearby">
      {entry.nearby.map(item => <li key={item.anatomyId}>
        <i style={{ background: structureColor(item.anatomyId, item.kind) }} aria-hidden="true" />
        <span className="depth-nearby-name"><b>{item.english}</b>{showChinese && item.chinese && <small>{item.chinese}</small>}</span>
        <span className="depth-distance">{item.overlapsReference ? 'overlap' : `${formatCm(item.distanceCm)} cm`}</span>
        <span className="depth-direction">{item.direction
          ? <>{item.direction.en}{zh(item.direction.zh) && ` · ${item.direction.zh}`}<small>{item.direction.probeRelationEn}{zh(item.direction.probeRelationZh) && ` · ${item.direction.probeRelationZh}`}</small></>
          : <>Its mesh contains the reference (overlap){zh(' · 网格包含参照点（重叠）')}</>}</span>
      </li>)}
    </ul>
    {entry.notModeled.length > 0 && <>
      <h4 className="depth-subheading">Not in this model · 本模型未包含</h4>
      <ul className="depth-missing-list">{entry.notModeled.map(item => <li key={item.english}><b>{item.english}</b>{zh(item.chinese) && ` · ${item.chinese}`}<span>{item.note.en}{zh(` ${item.note.zh}`)}</span></li>)}</ul>
    </>}
    {entry.sourceComparison && <SourceComparison comparison={entry.sourceComparison} showChinese={showChinese} />}

    <p className="depth-caption">Model-based study reference. Not a needling path or needling depth. 模型学习参照，不是进针路径或进针深度。</p>
    <p className="tiny">Distances are original model metres × 100 (cm), measured along the probe from the first modeled surface (depth 0). Skin and subcutaneous fat are not modeled, so a depth from the skin would be greater.{zh(' 距离为原始模型米数 × 100（厘米），沿探针从第一个建模表面（深度 0）量起。模型不含皮肤与皮下脂肪，从皮肤量起会更深。')}</p>
    <details className="depth-details">
      <summary>How the probe was built · 探针的建立方法</summary>
      <p>{axis.rationale.en}</p>
      {showChinese && <p>{axis.rationale.zh}</p>}
      <p>The probe is {axis.angleToEntrySurfaceNormalDeg}° from the outer-surface normal where it enters{bone ? ` and ${axis.firstBoneSurface!.angleToSurfaceNormalDeg}° from the ${bone.english.toLowerCase()} surface normal` : ''}. With 1.5–3 cm surface patches, the reference depth is {depthRange} cm{axis.sensitivity.sameLayerSequence ? ' and the layer order is unchanged' : `; one patch size adds or drops a thin layer (${axis.sensitivity.layerSequences.join(' / ')})`}.{zh(` 探针与入口处外表面法线相差 ${axis.angleToEntrySurfaceNormalDeg}°${bone ? `，与${bone.chinese || bone.english}表面法线相差 ${axis.firstBoneSurface!.angleToSurfaceNormalDeg}°` : ''}。表面取样半径改为 1.5–3 cm 时，参照点深度为 ${depthRange} cm${axis.sensitivity.sameLayerSequence ? '，层次顺序不变' : '，个别取样会增减一层薄层'}。`)}</p>
      <ul>{entry.limitations.map(item => <li key={item.en}>{item.en}{zh(` ${item.zh}`)}</li>)}</ul>
      <a href="./acupoint-depth.json" target="_blank" rel="noreferrer">Depth data (JSON) · 深浅数据 ↗</a>
    </details>
  </section>;
}

/** The probe compared with a published layer description for the point (sources listed below it). */
function SourceComparison({ comparison, showChinese }: { comparison: DepthSourceComparison; showChinese: boolean }) {
  const zh = (text?: string) => (showChinese && text ? text : '');
  const same = comparison.agreement === 'same-order';
  return <>
    <h4 className="depth-subheading">Compared with published layers · 与资料层次对照 <small>{same ? 'The listed muscles lie on the probe in the same order.' : 'The probe differs from the published layers.'}{zh(same ? ' 资料所列肌肉在探针上的顺序一致。' : ' 探针与资料层次不同。')}</small></h4>
    <p className="tiny">{comparison.sequence.en}{showChinese && <><br />{comparison.sequence.zh}</>}</p>
    <ul className="depth-nearby">
      {comparison.muscles.map(muscle => <li key={muscle.match}>
        <i style={{ background: structureColor(muscle.onProbe ? muscle.layerIds[0] : muscle.closestPartId, 'muscle') }} aria-hidden="true" />
        <span className="depth-nearby-name"><b>{muscle.english}</b>{showChinese && muscle.chinese && <small>{muscle.chinese}</small>}</span>
        <span className="depth-distance">{muscle.onProbe ? `${formatCm(muscle.entryCm)}–${formatCm(muscle.exitCm)} cm` : `${formatCm(muscle.distanceToProbeCm)} cm away`}</span>
        <span className="depth-direction">{muscle.onProbe
          ? <>On the probe{zh(' · 在探针上')}</>
          : <>Not on the probe; nearest {muscle.atProbeDepthCm < 0 ? `${formatCm(-muscle.atProbeDepthCm)} cm outside the first modeled surface` : `at ${formatCm(muscle.atProbeDepthCm)} cm depth`}, {muscle.direction.en.toLowerCase()} of it{muscle.closestPartEnglish !== muscle.english ? ` (${muscle.closestPartEnglish})` : ''}{zh(` · 不在探针上；最近处${muscle.atProbeDepthCm < 0 ? `在第一个建模表面外 ${formatCm(-muscle.atProbeDepthCm)} cm` : `在深度 ${formatCm(muscle.atProbeDepthCm)} cm`}，位于探针${muscle.direction.zh}`)}</>}</span>
      </li>)}
    </ul>
    {(comparison.modelOnlyMuscles.length > 0 || comparison.notes.length > 0) && <ul className="depth-missing-list">
      {comparison.modelOnlyMuscles.map(muscle => <li key={muscle.anatomyId}><b>{muscle.english}</b>{zh(muscle.chinese) && ` · ${muscle.chinese}`} {formatCm(muscle.entryCm)}–{formatCm(muscle.exitCm)} cm<span>On the probe in this model but not in the published layers.{zh(' 在本模型探针上，但资料层次未列出。')}</span></li>)}
      {comparison.notes.map(note => <li key={note.en}><span>{note.en}{zh(` ${note.zh}`)}</span></li>)}
    </ul>}
    <details className="depth-details">
      <summary>Sources for the layers · 层次资料来源</summary>
      <ul>{comparison.sources.map(source => <li key={source.url}><a href={source.url} target="_blank" rel="noreferrer">{source.title}</a> · {source.publisher} · accessed{zh(' · 查阅')} {source.accessed}<br />{source.supports.en}{zh(` ${source.supports.zh}`)}</li>)}</ul>
    </details>
  </>;
}

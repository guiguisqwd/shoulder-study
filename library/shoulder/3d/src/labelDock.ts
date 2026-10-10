import { useEffect, useState, type RefObject } from 'react';
import type { VanatomeAnnotation } from './vendor/types';

/** Estimated docked label height (px) in the vendor label column (AnnotationLayer): rows under 46 px use the compact style. */
export function dockLabelHeight(label: string, rowHeight: number) {
  const compact = rowHeight < 46;
  const lines = label.split('\n').reduce((total, line) => {
    const width = [...line].reduce((sum, char) => sum + (/[⺀-鿿＀-￯]/.test(char) ? (compact ? 10 : 11) : compact ? 5.6 : 6.1), 0);
    return total + Math.max(1, Math.ceil(width / 152));
  }, 0);
  return compact ? lines * 12 + 6 : lines * 16.5 + 10;
}

export type DockCandidate = { annotation: VanatomeAnnotation; priority: number; y: number };

/** The highest-priority labels (lowest number first) that fit the scene's label column without overlapping,
 * docked top to bottom by height (y). The column is the scene height minus 100 px (AnnotationLayer), and every
 * docked label is at least min(42, row - 3) px tall there, so a label never counts as shorter than that. */
export function fitDockedLabels(candidates: DockCandidate[], sceneHeight: number): VanatomeAnnotation[] {
  const usable = Math.max(0, sceneHeight - 100);
  const ranked = [...candidates].sort((a, b) => a.priority - b.priority);
  let shown: DockCandidate[] = [];
  for (let count = ranked.length; count >= 1 && !shown.length; count--) {
    const trial = ranked.slice(0, count).sort((a, b) => b.y - a.y || a.priority - b.priority);
    const row = Math.min(50, usable / count);
    const minHeight = Math.max(0, Math.min(42, row - 3));
    const heights = trial.map(item => Math.max(minHeight, dockLabelHeight(item.annotation.label, row)));
    // Neighbouring labels sit one row apart (centre to centre), so their half-heights must fit in one row.
    if (count === 1 || heights.every((height, index) => index === 0 || (heights[index - 1] + height) / 2 <= row)) shown = trial;
  }
  return shown.map((item, index) => ({ ...item.annotation, labelDockIndex: index, labelDockCount: shown.length }));
}

/** Height of an element in px, kept up to date while it resizes (0 before it mounts). */
export function useElementHeight(ref: RefObject<HTMLElement | null>) {
  const [height, setHeight] = useState(0);
  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    const update = () => setHeight(element.clientHeight);
    update();
    const observer = new ResizeObserver(update);
    observer.observe(element);
    return () => observer.disconnect();
  }, [ref]);
  return height;
}

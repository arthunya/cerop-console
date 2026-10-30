import { useEffect, useRef, useState } from "react";

const STEPS = [
  {
    title: "What CEROP is",
    body: <>Two machine-learning models built in a graduate course. One estimates whether a <b>supplier</b> may go bankrupt.
      The other estimates whether a <b>shipment</b> will arrive late. Each score comes with the reasons behind it.</>,
  },
  {
    title: "What you can do here",
    body: <>Browse real test cases and see why each one was scored the way it was. Drag the shipment threshold to see how many late
      orders get caught and how many false alarms come with them. Change a supplier's ratios and watch its score move.</>,
  },
  {
    title: "How to read a score",
    body: <>A score is the model's estimate of the chance something goes wrong. <b>High risk</b> means it crossed the decision threshold,
      <b> Watch</b> means it's at least half way there, <b>Clear</b> means it's well below. Each band has its own icon and label, so it doesn't rely on color.
      <br /><br /><span className="small">Synthetic data? No. These are real held-out test cases from public datasets that the models never saw during training.</span></>,
  },
];

export default function Intro({ onClose }) {
  const [i, setI] = useState(0);
  const ref = useRef(null);
  useEffect(() => {
    ref.current?.focus();
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  const last = i === STEPS.length - 1;
  return (
    <div className="intro-backdrop" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="intro" role="dialog" aria-modal="true" aria-labelledby="intro-title" tabIndex={-1} ref={ref}>
        <div className="dots" aria-hidden="true">{STEPS.map((_, k) => <i key={k} className={k <= i ? "on" : ""} />)}</div>
        <div className="small muted">Start here · {i + 1} of {STEPS.length}</div>
        <h2 id="intro-title">{STEPS[i].title}</h2>
        <p>{STEPS[i].body}</p>
        <div className="actions">
          <button className="btn sm" onClick={onClose}>Skip</button>
          <div className="row">
            {i > 0 && <button className="btn sm" onClick={() => setI(i - 1)}>Back</button>}
            <button className="btn sm primary" onClick={() => (last ? onClose() : setI(i + 1))}>{last ? "Start exploring" : "Next"}</button>
          </div>
        </div>
      </div>
    </div>
  );
}

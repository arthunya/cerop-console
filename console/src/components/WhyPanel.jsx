import { Band } from "./ui.jsx";
import { pts, pct, CELL_TEXT } from "../data.js";

// Shows one case's real SHAP explanation: base rate, the top drivers, the remainder, the score.
// Base + every row shown = the model's probability (checked in notebook 07 to within 1e-6).
export function WhyPanel({ c, base, kind, scoreOverride }) {
  const rows = [...c.drivers, { label: c.rest.label, contribution: c.rest.contribution, rest: true }];
  const maxAbs = Math.max(...rows.map((r) => Math.abs(r.contribution)), 0.01);
  const shown = scoreOverride ?? c.proba;
  return (
    <div className="why">
      <div className="top">
        <div>
          <div className="small muted">{kind === "fin" ? "Bankruptcy risk score" : "Late-delivery risk score"}</div>
          <div className="big">{pct(shown)}</div>
        </div>
        <div style={{ textAlign: "right" }}>
          <Band band={c.band} />
          <div className="small muted" style={{ marginTop: 6 }}>
            Actual outcome: {c.label === 1 ? (kind === "fin" ? "went bankrupt" : "arrived late") : (kind === "fin" ? "stayed solvent" : "arrived on time")}
          </div>
          <div className="small muted">{CELL_TEXT[c.cell]}</div>
        </div>
      </div>
      <table>
        <caption className="sr-only">Contribution of each factor to the score, in percentage points</caption>
        <tbody>
          <tr className="base"><td className="lab">Starting point (average {kind === "fin" ? "firm" : "order"})</td><td className="bar" /><td className="pts">{(base * 100).toFixed(1)}</td></tr>
          {rows.map((r) => {
            const w = `${(Math.abs(r.contribution) / maxAbs) * 50}%`;
            return (
              <tr key={r.label} className={r.rest ? "rest" : ""}>
                <td className="lab">
                  {r.label}
                  {r.value !== undefined && <small>{r.value}</small>}
                  {r.raw_value !== undefined && <small>value {r.raw_value.toPrecision(4)}</small>}
                </td>
                <td className="bar"><div className="cbar"><i className={r.contribution >= 0 ? "up" : "down"} style={{ width: w }} /></div></td>
                <td className="pts">{pts(r.contribution)}</td>
              </tr>
            );
          })}
          <tr className="final"><td className="lab">Model score</td><td className="bar" /><td className="pts">{(c.proba * 100).toFixed(1)}</td></tr>
        </tbody>
      </table>
      <div className="legend">
        <span><i style={{ background: "var(--series-2)" }} />pushes risk up</span>
        <span><i style={{ background: "var(--series-1)" }} />pulls risk down</span>
        <span>Numbers are percentage points.</span>
      </div>
    </div>
  );
}

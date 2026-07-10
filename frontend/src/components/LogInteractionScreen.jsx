import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { selectHcp } from "../store/hcpsSlice";
import { loadInteractions } from "../store/interactionsSlice";
import StructuredForm from "./StructuredForm";
import ChatInterface from "./ChatInterface";
import "./LogInteractionScreen.css";

export default function LogInteractionScreen() {
  const dispatch = useDispatch();
  const { list: hcps, selectedHcpId } = useSelector((s) => s.hcps);
  const { list: interactions } = useSelector((s) => s.interactions);

  useEffect(() => {
    if (selectedHcpId) dispatch(loadInteractions(selectedHcpId));
  }, [selectedHcpId, dispatch]);

  const selectedHcp = hcps.find((h) => h.id === selectedHcpId);

  return (
    <div className="log-screen">
      <div className="log-screen__top">
        <div>
          <h1 className="log-screen__title">Log Interaction</h1>
          <p className="log-screen__subtitle">
            Capture a visit, call, or email with a Healthcare Professional.
          </p>
        </div>

        <div className="hcp-select">
          <label htmlFor="hcp-select">HCP</label>
          <select
            id="hcp-select"
            value={selectedHcpId || ""}
            onChange={(e) => dispatch(selectHcp(Number(e.target.value)))}
          >
            {hcps.map((h) => (
              <option key={h.id} value={h.id}>
                {h.name} &middot; {h.specialty}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="log-screen__split">
        <div className="log-screen__split-left">
          <StructuredForm hcpId={selectedHcpId} />
        </div>
        <div className="log-screen__split-right">
          <ChatInterface hcpId={selectedHcpId} hcpName={selectedHcp?.name} />
        </div>
      </div>

      <section className="recent-interactions">
        <h2>Recent interactions {selectedHcp ? `with ${selectedHcp.name}` : ""}</h2>
        {interactions.length === 0 && (
          <p className="empty-state">No interactions logged yet for this HCP.</p>
        )}
        <ul className="interaction-list">
          {interactions.map((i) => (
            <li key={i.id} className="interaction-card">
              <div className="interaction-card__meta">
                <span className="pill">{i.interaction_type}</span>
                {i.sentiment && (
                  <span className={`pill pill--sentiment-${i.sentiment}`}>{i.sentiment}</span>
                )}
                <span className="interaction-card__date">
                  {i.interaction_date ? new Date(i.interaction_date).toLocaleString() : ""}
                </span>
              </div>
              <p className="interaction-card__summary">{i.summary || i.raw_notes}</p>
              {i.products_discussed && i.products_discussed.length > 0 && (
                <p className="interaction-card__row">
                  <strong>Products:</strong> {i.products_discussed.join(", ")}
                </p>
              )}
              {i.follow_up_actions && i.follow_up_actions.length > 0 && (
                <p className="interaction-card__row">
                  <strong>Follow-ups:</strong>{" "}
                  {i.follow_up_actions.map((f) => f.action).join("; ")}
                </p>
              )}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
import React, { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { submitInteraction } from "../store/interactionsSlice";
import "./StructuredForm.css";

const INTERACTION_TYPES = ["visit", "call", "email", "event", "sample_drop"];
const CHANNELS = ["in_person", "virtual", "phone", "email"];

export default function StructuredForm({ hcpId }) {
  const dispatch = useDispatch();
  const status = useSelector((s) => s.interactions.status);
  const lastSubmitted = useSelector((s) => s.interactions.lastSubmitted);

  const [interactionType, setInteractionType] = useState("visit");
  const [channel, setChannel] = useState("in_person");
  const [notes, setNotes] = useState("");
  const [attendees, setAttendees] = useState("");
  const [materialsShared, setMaterialsShared] = useState("");
  const [outcomes, setOutcomes] = useState("");
  const [sentiment, setSentiment] = useState("");

  // Auto-fill fields whenever the AI produces a new record (e.g. via chat)
  useEffect(() => {
    if (!lastSubmitted) return;
    if (lastSubmitted.summary) setNotes(lastSubmitted.summary);
    if (lastSubmitted.interaction_type) setInteractionType(lastSubmitted.interaction_type);
    if (lastSubmitted.channel) setChannel(lastSubmitted.channel);
    if (lastSubmitted.attendees) setAttendees(lastSubmitted.attendees.join(", "));
    if (lastSubmitted.materials_shared) setMaterialsShared(lastSubmitted.materials_shared.join(", "));
    if (lastSubmitted.outcomes) setOutcomes(lastSubmitted.outcomes);
    if (lastSubmitted.sentiment) setSentiment(lastSubmitted.sentiment);
  }, [lastSubmitted]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!hcpId || !notes.trim()) return;
    dispatch(
      submitInteraction({
        hcp_id: hcpId,
        interaction_type: interactionType,
        channel,
        raw_notes: notes,
        attendees: attendees ? attendees.split(",").map((a) => a.trim()).filter(Boolean) : [],
        materials_shared: materialsShared
          ? materialsShared.split(",").map((m) => m.trim()).filter(Boolean)
          : [],
        outcomes,
        sentiment: sentiment || undefined,
        created_by: "demo_rep",
      })
    );
  };

  return (
    <form className="structured-form" onSubmit={handleSubmit}>
      <div className="form-row">
        <div className="form-field">
          <label>Interaction type</label>
          <select value={interactionType} onChange={(e) => setInteractionType(e.target.value)}>
            {INTERACTION_TYPES.map((t) => (
              <option key={t} value={t}>
                {t.replace("_", " ")}
              </option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label>Channel</label>
          <select value={channel} onChange={(e) => setChannel(e.target.value)}>
            {CHANNELS.map((c) => (
              <option key={c} value={c}>
                {c.replace("_", " ")}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="form-field">
        <label>Attendees</label>
        <input
          type="text"
          placeholder="e.g. Dr. Kapoor, Nurse Singh"
          value={attendees}
          onChange={(e) => setAttendees(e.target.value)}
        />
        <p className="form-hint">Comma-separated names.</p>
      </div>

      <div className="form-field">
        <label>Notes</label>
        <textarea
          rows={6}
          placeholder="e.g. Discussed Drug A's latest cardiology efficacy data, dropped 10 samples. Dr. Mehta wants updated pediatric dosing info by next week."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
        <p className="form-hint">
          Fill this in manually, or describe the visit in the AI Assistant chat on the
          right &mdash; either way, the extracted record below updates automatically.
        </p>
      </div>

      <div className="form-field">
        <label>Materials shared</label>
        <input
          type="text"
          placeholder="e.g. Brochures, Sample kit"
          value={materialsShared}
          onChange={(e) => setMaterialsShared(e.target.value)}
        />
        <p className="form-hint">Comma-separated items.</p>
      </div>

      <div className="form-field">
        <label>Observed / inferred HCP sentiment</label>
        <div className="sentiment-radios">
          {["positive", "neutral", "negative"].map((s) => (
            <label key={s} className="sentiment-radio">
              <input
                type="radio"
                name="sentiment"
                value={s}
                checked={sentiment === s}
                onChange={(e) => setSentiment(e.target.value)}
              />
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </label>
          ))}
        </div>
      </div>

      <div className="form-field">
        <label>Outcomes</label>
        <textarea
          rows={3}
          placeholder="Key outcomes or agreements..."
          value={outcomes}
          onChange={(e) => setOutcomes(e.target.value)}
        />
      </div>

      <button className="btn-primary" type="submit" disabled={status === "submitting" || !hcpId}>
        {status === "submitting" ? "Logging with AI agent..." : "Log Interaction"}
      </button>

      {lastSubmitted && (
        <div className="ai-result">
          <h3>AI-extracted record</h3>
          <p><strong>Summary:</strong> {lastSubmitted.summary}</p>
          <p><strong>Sentiment:</strong> {lastSubmitted.sentiment}</p>
          <p><strong>Products discussed:</strong> {(lastSubmitted.products_discussed || []).join(", ") || "none"}</p>
          <p><strong>Samples dropped:</strong> {JSON.stringify(lastSubmitted.samples_dropped || {})}</p>
          <p><strong>Follow-ups:</strong> {(lastSubmitted.follow_up_actions || []).map(f => f.action).join("; ") || "none"}</p>
          <p><strong>Attendees:</strong> {(lastSubmitted.attendees || []).join(", ") || "none"}</p>
          <p><strong>Materials shared:</strong> {(lastSubmitted.materials_shared || []).join(", ") || "none"}</p>
          <p><strong>Outcomes:</strong> {lastSubmitted.outcomes || "none"}</p>
        </div>
      )}
    </form>
  );
}
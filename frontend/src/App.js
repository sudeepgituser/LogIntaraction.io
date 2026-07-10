import React, { useEffect } from "react";
import { useDispatch } from "react-redux";
import { loadHCPs } from "./store/hcpsSlice";
import LogInteractionScreen from "./components/LogInteractionScreen";
import "./App.css";

function App() {
  const dispatch = useDispatch();

  useEffect(() => {
    dispatch(loadHCPs());
  }, [dispatch]);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header__brand">
          <span className="app-header__mark">HCP</span>
          <span className="app-header__title">AI-First CRM &middot; HCP Module</span>
        </div>
      </header>
      <main className="app-main">
        <LogInteractionScreen />
      </main>
    </div>
  );
}

export default App;

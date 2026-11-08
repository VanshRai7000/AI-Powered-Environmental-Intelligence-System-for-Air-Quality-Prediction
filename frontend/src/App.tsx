import { useEffect, useState } from "react";
import { checkBackendHealth } from "./services/health";

function App() {
  const [status, setStatus] = useState("Checking backend...");

  useEffect(() => {
    checkBackendHealth()
      .then((data) => {
        setStatus(data.status);
      })
      .catch(() => {
        setStatus("Backend unavailable");
      });
  }, []);

  return (
    <div>
      <h1>Environmental Intelligence System</h1>
      <p>Backend status: {status}</p>
    </div>
  );
}

export default App;
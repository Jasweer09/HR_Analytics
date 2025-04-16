import React, { useState } from 'react';
import EmployeeForm from './components/EmployeeForm';
import PredictionResults from './components/PredictionResults';
import 'bootstrap/dist/css/bootstrap.min.css';

function App() {
  const [predictions, setPredictions] = useState(null);

  const handlePredict = (results) => {
    setPredictions(results);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-blue-600 text-white p-6 shadow-md">
        <h1 className="text-3xl font-bold">HR Analytics Dashboard</h1>
        <p className="mt-2 text-sm">Predict Attrition, Performance, and Retention Risk for Employees</p>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto p-6">
        <EmployeeForm onPredict={handlePredict} />
        {predictions && <PredictionResults predictions={predictions} />}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white p-4 text-center">
        <p>© 2025 HR Analytics. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default App;
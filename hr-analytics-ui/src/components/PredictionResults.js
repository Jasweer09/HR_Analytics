import React from 'react';

const PredictionResults = ({ predictions }) => {
  const { attrition, performance, retention } = predictions;

  return (
    <div className="mt-8">
      <h2 className="text-2xl font-semibold mb-4">Prediction Results</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Attrition Risk */}
        <div className="bg-white p-4 rounded-lg shadow-md hover:scale-105 transition-transform">
          <h3 className="text-lg font-medium">Attrition Risk</h3>
          <p className={`mt-2 text-lg ${attrition.AttritionRisk === 1 ? 'text-red-500' : 'text-green-600'}`}>
            {attrition.AttritionRisk === 1 ? 'High' : 'Low'}
          </p>
          <p className="text-sm text-gray-600">
            Probability: {(attrition.AttritionRiskProbability * 100).toFixed(2)}%
          </p>
        </div>

        {/* Performance Rating */}
        <div className="bg-white p-4 rounded-lg shadow-md hover:scale-105 transition-transform">
          <h3 className="text-lg font-medium">Performance Rating</h3>
          <p className="mt-2 text-lg text-blue-600">
            {performance.PerformanceRating >= 3 ? `High (${performance.PerformanceRating})` : `Low (${performance.PerformanceRating})`}
          </p>
        </div>

        {/* Retention Risk */}
        <div className="bg-white p-4 rounded-lg shadow-md hover:scale-105 transition-transform">
          <h3 className="text-lg font-medium">Retention Risk</h3>
          <p className={`mt-2 text-lg ${retention.RetentionRisk === 1 ? 'text-red-500' : 'text-green-600'}`}>
            {retention.RetentionRisk === 1 ? 'High' : 'Low'}
          </p>
          <p className="text-sm text-gray-600">
            Probability: {(retention.RetentionRiskProbability * 100).toFixed(2)}%
          </p>
        </div>
      </div>
    </div>
  );
};

export default PredictionResults;
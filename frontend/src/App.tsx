import React, { Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import DashboardLayout from './components/layout/DashboardLayout';
import DependencyGraphViewer from './pages/DependencyGraphViewer';
import BRepGeometryPage from './pages/BRepGeometryPage';

const App: React.FC = () => {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-screen bg-gray-900 text-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-lg">Loading...</p>
        </div>
      </div>
    }>
      <Routes>
        <Route path="/" element={<DashboardLayout />} />
        <Route path="/dependency-graph" element={<DependencyGraphViewer />} />
        <Route path="/brep-geometry" element={<BRepGeometryPage />} />
      </Routes>
    </Suspense>
  );
};

export default App;

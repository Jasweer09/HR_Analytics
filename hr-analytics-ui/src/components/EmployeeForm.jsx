import React, { useState, useEffect } from "react";
import axios from "axios";
import { jsPDF } from "jspdf";
import { Bar, Doughnut, Radar, Pie, Line, Scatter } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  RadialLinearScale,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import * as XLSX from "xlsx";
import { Nav, Button, Form, Spinner, InputGroup } from "react-bootstrap";
import { motion } from "framer-motion";
import {
  FaEnvelope,
  FaFilePdf,
  FaFileExcel,
  FaChartBar,
  FaUndo,
  FaSun,
  FaMoon,
  FaUser,
  FaUsers,
  FaExclamationTriangle,
  FaStar,
  FaChartLine,
  FaUpload,
} from "react-icons/fa";
import Confetti from "react-confetti";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  RadialLinearScale,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const EmployeeForm = () => {
  const [tab, setTab] = useState("individual");
  const [theme, setTheme] = useState("light");
  const [formData, setFormData] = useState({
    Age: 35,
    Gender: "Male",
    Department: "Sales",
    JobRole: "Manager",
    MonthlyIncome: 10000,
    YearsAtCompany: 10,
    OverTime: "No",
    JobSatisfaction: 5,
    WorkLifeBalance: 5,
    TotalWorkingYears: 15,
    TrainingTimesLastYear: 5,
    JobInvolvement: 5,
    EnvironmentSatisfaction: 5,
    RelationshipSatisfaction: 5,
  });
  const [formErrors, setFormErrors] = useState({});
  const [predictions, setPredictions] = useState(null);
  const [bulkPredictions, setBulkPredictions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [predictionHistory, setPredictionHistory] = useState([]);
  const [csvFile, setCsvFile] = useState(null);
  const [email, setEmail] = useState("");
  const [summaryReport, setSummaryReport] = useState(null);
  const [showConfetti, setShowConfetti] = useState(false);

  useEffect(() => {
    const savedHistory = localStorage.getItem("predictionHistory");
    if (savedHistory) setPredictionHistory(JSON.parse(savedHistory));
    document.body.className = theme;
  }, [theme]);

  useEffect(() => {
    localStorage.setItem("predictionHistory", JSON.stringify(predictionHistory));
  }, [predictionHistory]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: parseInt(value, 10) || value });
    const errors = { ...formErrors };
    if (name === "Age" && (value < 18 || value > 100)) errors.Age = "Age must be between 18 and 100.";
    else if (name === "Age") delete errors.Age;
    if (name === "MonthlyIncome" && value <= 0) errors.MonthlyIncome = "Monthly Income must be greater than 0.";
    else if (name === "MonthlyIncome") delete errors.MonthlyIncome;
    if (name === "YearsAtCompany" && value < 0) errors.YearsAtCompany = "Years at Company cannot be negative.";
    else if (name === "YearsAtCompany") delete errors.YearsAtCompany;
    setFormErrors(errors);
  };

  const validateForm = () => {
    const errors = [];
    if (formData.Age < 18 || formData.Age > 100) errors.push("Age must be between 18 and 100.");
    if (formData.MonthlyIncome <= 0) errors.push("Monthly Income must be greater than 0.");
    if (formData.YearsAtCompany < 0) errors.push("Years at Company cannot be negative.");
    return errors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const validationErrors = validateForm();
    if (validationErrors.length > 0) {
      setError(validationErrors.join(" "));
      setLoading(false);
      toast.error(validationErrors.join(" "));
      return;
    }

    console.log("Form Data Sent to Server:", JSON.stringify(formData, null, 2));

    try {
      const responseAttrition = await axios.post("https://hr-analytics-attrition.onrender.com/predict_attrition", formData);
      const responsePerformance = await axios.post("https://hr-analytics-performance-retention.onrender.com/predict_performance", formData);
      const responseRetention = await axios.post("https://hr-analytics-performance-retention.onrender.com/predict_retention", formData);

      console.log("Attrition Response:", JSON.stringify(responseAttrition.data, null, 2));
      console.log("Performance Response:", JSON.stringify(responsePerformance.data, null, 2));
      console.log("Retention Response:", JSON.stringify(responseRetention.data, null, 2));

      const newPrediction = {
        timestamp: new Date().toLocaleString(),
        formData: { ...formData },
        predictions: {
          attrition: responseAttrition.data,
          performance: responsePerformance.data,
          retention: responseRetention.data,
        },
      };

      setPredictions(newPrediction.predictions);
      setPredictionHistory([newPrediction, ...predictionHistory]);
      setShowConfetti(true);
      toast.success("Prediction completed successfully!");
    } catch (err) {
      setError(`Error fetching predictions: ${err.response?.status || "Unknown"} - ${err.response?.statusText || "Server Error"}`);
      toast.error("Error fetching predictions.");
      console.error("Axios Error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleBulkSubmit = async (e) => {
    e.preventDefault();
    if (!csvFile) {
      setError("Please upload a CSV file.");
      toast.error("Please upload a CSV file.");
      return;
    }

    setError(null);
    setLoading(true);

    const formData = new FormData();
    formData.append("file", csvFile);

    try {
      const responseAttrition = await axios.post("https://hr-analytics-attrition.onrender.com/predict_attrition_bulk", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const responsePerformance = await axios.post("https://hr-analytics-performance-retention.onrender.com/predict_performance_bulk", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const responseRetention = await axios.post("https://hr-analytics-performance-retention.onrender.com/predict_retention_bulk", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const bulkResults = {
        attrition: responseAttrition.data.predictions,
        performance: responsePerformance.data.predictions,
        retention: responseRetention.data.predictions,
      };

      setBulkPredictions(bulkResults);

      const highAttritionCount = bulkResults.attrition.filter((pred) => pred.AttritionRisk === 1).length;
      const avgPerformance =
        bulkResults.performance.reduce((sum, pred) => sum + pred.PerformanceRating, 0) /
        bulkResults.performance.length;
      const highRetentionRiskCount = bulkResults.retention.filter((pred) => pred.RetentionRisk === 1).length;

      setSummaryReport({
        totalEmployees: bulkResults.attrition.length,
        highAttritionCount,
        avgPerformance: avgPerformance.toFixed(2),
        highRetentionRiskCount,
      });

      setPredictionHistory([...predictionHistory, { timestamp: new Date().toLocaleString(), bulkData: bulkResults }]);
      setShowConfetti(true);
      toast.success("Bulk prediction completed successfully!");
    } catch (err) {
      setError(`Error processing bulk predictions: ${err.response?.status || "Unknown"} - ${err.response?.statusText || "Server Error"}`);
      toast.error("Error processing bulk predictions.");
      console.error("Axios Error:", err);
    } finally {
      setLoading(false);
    }
  };

  const exportToPDF = () => {
    if (!predictions) return;
    const doc = new jsPDF();
    doc.setFont("Inter", "normal");
    doc.setFontSize(16);
    doc.text("Employee Prediction Report", 20, 20);
    doc.setFontSize(12);
    doc.text(`Date: ${new Date().toLocaleString()}`, 20, 30);
    doc.setFontSize(14);
    doc.text("Employee Details:", 20, 40);
    doc.setFontSize(10);
    let y = 50;
    for (const [key, value] of Object.entries(formData)) {
      doc.text(`${key}: ${value}`, 20, y);
      y += 5;
    }
    doc.setFontSize(14);
    doc.text("Predictions:", 20, y + 10);
    doc.setFontSize(10);
    y += 20;
    doc.text(
      `Attrition Risk: ${predictions.attrition.AttritionRisk === 1 ? "High" : "Low"} (Probability: ${
        (predictions.attrition.AttritionRiskProbability * 100).toFixed(2)
      }%)`,
      20,
      y
    );
    y += 5;
    doc.text(`Performance Rating: ${predictions.performance.PerformanceRating}/5`, 20, y);
    y += 5;
    doc.text(
      `Retention Risk: ${predictions.retention.RetentionRisk === 1 ? "High" : "Low"} (Probability: ${
        (predictions.retention.RetentionRiskProbability * 100).toFixed(2)
      }%)`,
      20,
      y
    );
    doc.save("prediction_report.pdf");
    toast.success("PDF exported successfully!");
  };

  const exportBulkToExcel = () => {
    if (!bulkPredictions) return;
    const data = bulkPredictions.attrition.map((_, idx) => ({
      EmployeeIndex: idx,
      AttritionRisk: bulkPredictions.attrition[idx].AttritionRisk,
      AttritionRiskProbability: bulkPredictions.attrition[idx].AttritionRiskProbability,
      PerformanceRating: bulkPredictions.performance[idx].PerformanceRating,
      RetentionRisk: bulkPredictions.retention[idx].RetentionRisk,
      RetentionRiskProbability: bulkPredictions.retention[idx].RetentionRiskProbability,
    }));
    const ws = XLSX.utils.json_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Predictions");
    XLSX.writeFile(wb, "bulk_predictions.xlsx");
    toast.success("Excel file exported successfully!");
  };

  const exportSummaryReport = () => {
    if (!summaryReport) return;
    const doc = new jsPDF();
    doc.setFont("Inter", "normal");
    doc.setFontSize(16);
    doc.text("Bulk Analytics Summary", 20, 20);
    doc.setFontSize(12);
    doc.text(`Date: ${new Date().toLocaleString()}`, 20, 30);
    doc.setFontSize(14);
    doc.text("Summary Statistics:", 20, 40);
    doc.setFontSize(10);
    doc.text(`Total Employees: ${summaryReport.totalEmployees}`, 20, 50);
    doc.text(`High Attrition Risk: ${summaryReport.highAttritionCount}`, 20, 60);
    doc.text(`Average Performance: ${summaryReport.avgPerformance}`, 20, 70);
    doc.text(`High Retention Risk: ${summaryReport.highRetentionRiskCount}`, 20, 80);
    doc.save("summary_report.pdf");
    toast.success("Summary exported successfully!");
  };

  const getPerformanceExplanation = () => {
    const rating = predictions?.performance.PerformanceRating;
    const maxRating = 5;
    if (rating >= 4) {
      return `This employee is performing exceptionally well with a rating of ${rating}/${maxRating}. They are highly engaged in their role as a ${formData.JobRole} in the ${formData.Department} department, contributing significantly to team goals. Their job satisfaction (${formData.JobSatisfaction}/5) and involvement (${formData.JobInvolvement}/5) suggest they enjoy their work and are motivated. However, their work-life balance (${formData.WorkLifeBalance}/5) should be monitored to prevent burnout, especially with overtime status (${formData.OverTime}).`;
    } else if (rating >= 3) {
      return `This employee’s performance is satisfactory at a rating of ${rating}/${maxRating}. Working as a ${formData.JobRole} in ${formData.Department}, they meet expectations but may lack the extra drive seen in top performers. Their satisfaction (${formData.JobSatisfaction}/5) and environment satisfaction (${formData.EnvironmentSatisfaction}/5) are decent, but low work-life balance (${formData.WorkLifeBalance}/5) or overtime (${formData.OverTime}) could be hindering higher output. Improvement is possible with support.`;
    } else {
      return `This employee is underperforming with a rating of ${rating}/${maxRating}. As a ${formData.JobRole} in ${formData.Department}, they struggle to meet expectations. Low job satisfaction (${formData.JobSatisfaction}/5), poor work-life balance (${formData.WorkLifeBalance}/5), and possibly excessive overtime (${formData.OverTime}) are likely contributors. This could lead to disengagement or turnover if not addressed promptly.`;
    }
  };

  const getAttritionExplanation = () => {
    const risk = predictions?.attrition.AttritionRisk;
    const prob = (predictions?.attrition.AttritionRiskProbability * 100).toFixed(2);
    if (risk === 1) {
      return `There’s a high chance (${prob}%) this employee might leave. Given their role as a ${formData.JobRole} with ${formData.YearsAtCompany} years at the company and a monthly income of $${formData.MonthlyIncome}, factors like low job satisfaction (${formData.JobSatisfaction}/5) or poor work-life balance (${formData.WorkLifeBalance}/5) could be driving this risk. Their overtime status (${formData.OverTime}) and environment satisfaction (${formData.EnvironmentSatisfaction}/5) suggest dissatisfaction or burnout. If unaddressed, this could lead to a loss of talent, increasing hiring costs.`;
    } else {
      return `The likelihood of this employee leaving is low (${prob}%). As a ${formData.JobRole} in ${formData.Department} with ${formData.YearsAtCompany} years of tenure, they seem stable. Their job satisfaction (${formData.JobSatisfaction}/5), work-life balance (${formData.WorkLifeBalance}/5), and income ($${formData.MonthlyIncome}) indicate they’re content. However, monitor overtime (${formData.OverTime}) to maintain this stability.`;
    }
  };

  const getRetentionExplanation = () => {
    const risk = predictions?.retention.RetentionRisk;
    const prob = (predictions?.retention.RetentionRiskProbability * 100).toFixed(2);
    const perf = predictions?.performance.PerformanceRating;
    if (risk === 1 && perf >= 4) {
      return `Despite a high retention risk (${prob}%), this employee is valuable with a performance rating of ${perf}/5. As a ${formData.JobRole}, their ${formData.YearsAtCompany} years of experience and $${formData.MonthlyIncome} income make them worth retaining. Low work-life balance (${formData.WorkLifeBalance}/5) or overtime (${formData.OverTime}) might push them away. To retain them, offer flexible hours, a raise, or recognition to boost their satisfaction (${formData.JobSatisfaction}/5).`;
    } else if (risk === 1) {
      return `This employee has a high retention risk (${prob}%) and a performance rating of ${perf}/5. Working as a ${formData.JobRole}, their tenure (${formData.YearsAtCompany} years) and satisfaction (${formData.JobSatisfaction}/5) suggest disengagement. Overtime (${formData.OverTime}) or poor environment satisfaction (${formData.EnvironmentSatisfaction}/5) could be factors. Retention may not be critical unless performance improves—consider training or reassignment.`;
    } else {
      return `Retention risk is low (${prob}%) for this ${formData.JobRole}. With a performance rating of ${perf}/5 and ${formData.YearsAtCompany} years at the company, they’re likely to stay. Their satisfaction (${formData.JobSatisfaction}/5) and work-life balance (${formData.WorkLifeBalance}/5) are positive indicators. Maintain this by ensuring overtime (${formData.OverTime}) doesn’t increase and their income ($${formData.MonthlyIncome}) remains competitive.`;
    }
  };

  const getBulkPerformanceBar = () => {
    if (!bulkPredictions) return null;
    const performanceCounts = [1, 2, 3, 4, 5].map(
      (rating) => bulkPredictions.performance.filter((pred) => pred.PerformanceRating === rating).length
    );
    return {
      labels: ["1", "2", "3", "4", "5"],
      datasets: [{ label: "Performance Distribution", data: performanceCounts, backgroundColor: "#3B82F6" }],
    };
  };

  const getBulkJobSatisfactionDoughnut = () => {
    if (!bulkPredictions) return null;
    const highSatisfaction = bulkPredictions.performance.filter((_, idx) => formData.JobSatisfaction >= 4).length;
    const lowSatisfaction = bulkPredictions.performance.length - highSatisfaction;
    return {
      labels: ["High (4-5)", "Low (1-3)"],
      datasets: [{ data: [highSatisfaction, lowSatisfaction], backgroundColor: ["#059669", "#EF4444"] }],
    };
  };

  const getBulkWorkLifeBalanceRadar = () => {
    if (!bulkPredictions) return null;
    const avgWorkLifeBalance = bulkPredictions.performance.reduce((sum, pred) => sum + formData.WorkLifeBalance, 0) / bulkPredictions.performance.length;
    return {
      labels: ["Work-Life Balance"],
      datasets: [
        {
          label: "Average",
          data: [avgWorkLifeBalance],
          backgroundColor: "rgba(6, 182, 212, 0.2)",
          borderColor: "#06B6D4",
          borderWidth: 2,
        },
      ],
    };
  };

  const getBulkAttritionPie = () => {
    if (!bulkPredictions) return null;
    const highAttrition = bulkPredictions.attrition.filter((pred) => pred.AttritionRisk === 1).length;
    const lowAttrition = bulkPredictions.attrition.length - highAttrition;
    return {
      labels: ["High Risk", "Low Risk"],
      datasets: [{ data: [highAttrition, lowAttrition], backgroundColor: ["#EF4444", "#059669"] }],
    };
  };

  const getBulkRetentionLine = () => {
    if (!bulkPredictions) return null;
    const retentionRisk = bulkPredictions.retention.map((pred) => pred.RetentionRiskProbability * 100);
    return {
      labels: Array.from({ length: retentionRisk.length }, (_, i) => `Emp ${i + 1}`),
      datasets: [{ label: "Retention Risk", data: retentionRisk, borderColor: "#F97316", fill: false }],
    };
  };

  const getBulkEngagementScatter = () => {
    if (!bulkPredictions) return null;
    return {
      datasets: [
        {
          label: "Engagement vs Performance",
          data: bulkPredictions.performance.map((pred, idx) => ({
            x: formData.JobInvolvement,
            y: pred.PerformanceRating,
          })),
          backgroundColor: "#3B82F6",
        },
      ],
    };
  };

  const getAnalyticsPerformanceBar = () => {
    const perfCounts = [1, 2, 3, 4, 5].map((rating) =>
      predictionHistory.reduce(
        (sum, entry) => sum + (entry.predictions?.performance?.PerformanceRating === rating ? 1 : 0) + (entry.bulkData?.performance?.filter((p) => p.PerformanceRating === rating).length || 0),
        0
      )
    );
    return {
      labels: ["1", "2", "3", "4", "5"],
      datasets: [{ label: "Performance Distribution", data: perfCounts, backgroundColor: "#3B82F6" }],
    };
  };

  const getAnalyticsJobSatisfactionDoughnut = () => {
    const highSatisfaction = predictionHistory.reduce(
      (sum, entry) => sum + (entry.formData?.JobSatisfaction >= 4 ? 1 : 0) + (entry.bulkData?.performance?.filter((_, idx) => entry.formData?.JobSatisfaction >= 4).length || 0),
      0
    );
    const total = predictionHistory.reduce((sum, entry) => sum + 1 + (entry.bulkData?.performance?.length || 0), 0);
    return {
      labels: ["High (4-5)", "Low (1-3)"],
      datasets: [{ data: [highSatisfaction, total - highSatisfaction], backgroundColor: ["#059669", "#EF4444"] }],
    };
  };

  const getAnalyticsWorkLifeBalanceRadar = () => {
    const avgWorkLifeBalance = predictionHistory.reduce(
      (sum, entry) => sum + (entry.formData?.WorkLifeBalance || 0) + (entry.bulkData?.performance?.reduce((s, p) => s + formData.WorkLifeBalance, 0) || 0),
      0
    ) / predictionHistory.reduce((sum, entry) => sum + 1 + (entry.bulkData?.performance?.length || 0), 0);
    return {
      labels: ["Work-Life Balance"],
      datasets: [
        {
          label: "Average",
          data: [avgWorkLifeBalance],
          backgroundColor: "rgba(6, 182, 212, 0.2)",
          borderColor: "#06B6D4",
          borderWidth: 2,
        },
      ],
    };
  };

  const getAnalyticsAttritionPie = () => {
    const highAttrition = predictionHistory.reduce(
      (sum, entry) => sum + (entry.predictions?.attrition?.AttritionRisk === 1 ? 1 : 0) + (entry.bulkData?.attrition?.filter((a) => a.AttritionRisk === 1).length || 0),
      0
    );
    const total = predictionHistory.reduce((sum, entry) => sum + 1 + (entry.bulkData?.attrition?.length || 0), 0);
    return {
      labels: ["High Risk", "Low Risk"],
      datasets: [{ data: [highAttrition, total - highAttrition], backgroundColor: ["#EF4444", "#059669"] }],
    };
  };

  const getAnalyticsRetentionLine = () => {
    const retentionRisk = predictionHistory.map((entry) =>
      entry.predictions?.retention?.RetentionRiskProbability * 100 || entry.bulkData?.retention?.reduce((sum, r) => sum + r.RetentionRiskProbability, 0) / (entry.bulkData?.retention?.length || 1) * 100
    );
    return {
      labels: predictionHistory.map((_, i) => `Prediction ${i + 1}`),
      datasets: [{ label: "Retention Risk Trend", data: retentionRisk, borderColor: "#F97316", fill: false }],
    };
  };

  const getAnalyticsEngagementScatter = () => {
    const data = predictionHistory.flatMap((entry) =>
      entry.bulkData?.performance?.map((p, idx) => ({ x: entry.formData?.JobInvolvement || 3, y: p.PerformanceRating })) || [
        { x: entry.formData?.JobInvolvement || 3, y: entry.predictions?.performance?.PerformanceRating },
      ]
    );
    return {
      datasets: [{ label: "Engagement vs Performance", data, backgroundColor: "#3B82F6" }],
    };
  };

  const renderRangeOptions = (start, end) => {
    return Array.from({ length: end - start + 1 }, (_, i) => (
      <option key={i + start} value={i + start}>{i + start}</option>
    ));
  };

  return (
    <div className={`dashboard-container ${theme}`}>
      <ToastContainer />
      {showConfetti && <Confetti recycle={false} numberOfPieces={200} />}
      
      <motion.header className="dashboard-header" initial={{ y: -100 }} animate={{ y: 0 }} transition={{ duration: 0.5 }}>
        <div className="header-left">
          <h1 className="header-title">HR Analytics</h1>
          <p className="header-subtitle">Data-Driven People Insights</p>
        </div>
        <div className="header-right">
          <Nav variant="pills" className="dashboard-tabs">
            <Nav.Item>
              <Nav.Link active={tab === "individual"} onClick={() => setTab("individual")}>
                <FaUser /> Individual
              </Nav.Link>
            </Nav.Item>
            <Nav.Item>
              <Nav.Link active={tab === "multiple"} onClick={() => setTab("multiple")}>
                <FaUsers /> Bulk
              </Nav.Link>
            </Nav.Item>
            <Nav.Item>
              <Nav.Link active={tab === "analytics"} onClick={() => setTab("analytics")}>
                <FaChartBar /> Analytics
              </Nav.Link>
            </Nav.Item>
          </Nav>
          <Button className="theme-toggle" onClick={() => setTheme(theme === "light" ? "dark" : "light")}>
            {theme === "light" ? <FaMoon /> : <FaSun />}
          </Button>
        </div>
      </motion.header>

      <main className="dashboard-main">
        {tab === "individual" && (
          <>
            <motion.div className="form-card" initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ duration: 0.5 }}>
              <h2><FaUser /> Employee Prediction</h2>
              {error && <p className="text-danger">{error}</p>}
              <Form onSubmit={handleSubmit}>
                <div className="form-grid">
                  {Object.keys(formData).map((key) => (
                    <Form.Group key={key} className="form-item">
                      <Form.Label>{key.replace(/([A-Z])/g, " $1").trim()}</Form.Label>
                      {["Gender", "Department", "JobRole", "OverTime"].includes(key) ? (
                        <Form.Select name={key} value={formData[key]} onChange={handleChange}>
                          {key === "Gender" && (
                            <>
                              <option value="Male">Male</option>
                              <option value="Female">Female</option>
                            </>
                          )}
                          {key === "Department" && (
                            <>
                              <option value="Sales">Sales</option>
                              <option value="Research & Development">R&D</option>
                              <option value="Human Resources">HR</option>
                            </>
                          )}
                          {key === "JobRole" && (
                            <>
                              <option value="Sales Executive">Sales Executive</option>
                              <option value="Research Scientist">Research Scientist</option>
                              <option value="Manager">Manager</option>
                            </>
                          )}
                          {key === "OverTime" && (
                            <>
                              <option value="Yes">Yes</option>
                              <option value="No">No</option>
                            </>
                          )}
                        </Form.Select>
                      ) : ["JobSatisfaction", "WorkLifeBalance", "JobInvolvement", "EnvironmentSatisfaction", "RelationshipSatisfaction"].includes(key) ? (
                        <Form.Select name={key} value={formData[key]} onChange={handleChange}>
                          {renderRangeOptions(1, 5)}
                        </Form.Select>
                      ) : ["TrainingTimesLastYear"].includes(key) ? (
                        <Form.Select name={key} value={formData[key]} onChange={handleChange}>
                          {renderRangeOptions(0, 5)}
                        </Form.Select>
                      ) : (
                        <Form.Control
                          type="number"
                          name={key}
                          value={formData[key]}
                          onChange={handleChange}
                          className={formErrors[key] ? "is-invalid" : ""}
                        />
                      )}
                      {formErrors[key] && <Form.Control.Feedback type="invalid">{formErrors[key]}</Form.Control.Feedback>}
                    </Form.Group>
                  ))}
                </div>
                <div className="form-actions">
                  <Button type="submit" disabled={loading}>
                    {loading ? <Spinner size="sm" /> : "Predict"}
                  </Button>
                  <Button variant="secondary" onClick={() => setFormData({ ...formData })}>
                    <FaUndo /> Reset
                  </Button>
                </div>
              </Form>
            </motion.div>

            {predictions && (
              <motion.div className="predictions-card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}>
                <h2><FaChartBar /> Prediction Insights</h2>
                <div className="predictions-grid">
                  <motion.div className="flip-card performance-card" whileHover={{ scale: 1.05 }} transition={{ duration: 0.3 }}>
                    <div className="flip-card-inner">
                      <div className="flip-card-front">
                        <FaStar />
                        <h3>Performance</h3>
                        <p>{predictions.performance.PerformanceRating}/5</p>
                      </div>
                      <div className="flip-card-back">
                        <p>Rating: {predictions.performance.PerformanceRating}</p>
                        <p>Raw Response: {JSON.stringify(predictions.performance)}</p>
                      </div>
                    </div>
                  </motion.div>
                  <motion.div className="flip-card attrition-card" whileHover={{ scale: 1.05 }} transition={{ duration: 0.3 }}>
                    <div className="flip-card-inner">
                      <div className="flip-card-front">
                        <FaExclamationTriangle />
                        <h3>Attrition</h3>
                        <p>{predictions.attrition.AttritionRisk === 1 ? "High" : "Low"}</p>
                      </div>
                      <div className="flip-card-back">
                        <p>Probability: {(predictions.attrition.AttritionRiskProbability * 100).toFixed(2)}%</p>
                      </div>
                    </div>
                  </motion.div>
                  <motion.div className="flip-card retention-card" whileHover={{ scale: 1.05 }} transition={{ duration: 0.3 }}>
                    <div className="flip-card-inner">
                      <div className="flip-card-front">
                        <FaChartLine />
                        <h3>Retention</h3>
                        <p>{predictions.retention.RetentionRisk === 1 ? "High Risk" : "Stable"}</p>
                      </div>
                      <div className="flip-card-back">
                        <p>Probability: {(predictions.retention.RetentionRiskProbability * 100).toFixed(2)}%</p>
                      </div>
                    </div>
                  </motion.div>
                </div>
                <div className="explanation-section">
                  <h3>Performance Overview</h3>
                  <p>{getPerformanceExplanation()}</p>
                  <h3>Attrition Risk</h3>
                  <p>{getAttritionExplanation()}</p>
                  <h3>Retention Strategy</h3>
                  <p>{getRetentionExplanation()}</p>
                </div>
                <div className="prediction-actions">
                  <InputGroup>
                    <Form.Control type="email" placeholder="Email report..." value={email} onChange={(e) => setEmail(e.target.value)} />
                    <Button onClick={() => toast.info("Email feature coming soon!")}>
                      <FaEnvelope />
                    </Button>
                  </InputGroup>
                  <Button onClick={exportToPDF}><FaFilePdf /> Export</Button>
                </div>
              </motion.div>
            )}
          </>
        )}

        {tab === "multiple" && (
          <>
            <motion.div className="upload-card" initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ duration: 0.5 }}>
              <h2><FaUpload /> Bulk Prediction</h2>
              {error && <p className="text-danger">{error}</p>}
              <Form onSubmit={handleBulkSubmit}>
                <Form.Group>
                  <Form.Label>Upload CSV</Form.Label>
                  <Form.Control type="file" accept=".csv" onChange={(e) => setCsvFile(e.target.files[0])} />
                </Form.Group>
                <Button type="submit" disabled={loading}>
                  {loading ? <Spinner size="sm" /> : "Process"}
                </Button>
              </Form>
            </motion.div>

            {bulkPredictions && summaryReport && (
              <motion.div className="bulk-results-card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}>
                <h2><FaUsers /> Bulk Insights</h2>
                <div className="plot-grid">
                  <div className="plot-item">
                    <Bar data={getBulkPerformanceBar()} options={{ responsive: true, plugins: { title: { display: true, text: "Performance Distribution" } } }} />
                  </div>
                  <div className="plot-item">
                    <Doughnut data={getBulkJobSatisfactionDoughnut()} options={{ responsive: true, plugins: { title: { display: true, text: "Job Satisfaction" } } }} />
                  </div>
                  <div className="plot-item">
                    <Radar data={getBulkWorkLifeBalanceRadar()} options={{ responsive: true, plugins: { title: { display: true, text: "Work-Life Balance" } } }} />
                  </div>
                  <div className="plot-item">
                    <Pie data={getBulkAttritionPie()} options={{ responsive: true, plugins: { title: { display: true, text: "Attrition Risk" } } }} />
                  </div>
                  <div className="plot-item">
                    <Line data={getBulkRetentionLine()} options={{ responsive: true, plugins: { title: { display: true, text: "Retention Risk Trend" } } }} />
                  </div>
                  <div className="plot-item">
                    <Scatter data={getBulkEngagementScatter()} options={{ responsive: true, plugins: { title: { display: true, text: "Engagement vs Performance" } } }} />
                  </div>
                </div>
                <div className="employee-list">
                  <h3>Employees Likely to Leave</h3>
                  <ul>
                    {bulkPredictions.attrition && bulkPredictions.performance
                      ? bulkPredictions.attrition
                          .map((pred, idx) => ({ pred, idx }))
                          .filter(({ pred, idx }) => pred.AttritionRisk === 1 && bulkPredictions.performance[idx]?.PerformanceRating >= 4)
                          .map(({ idx }) => {
                            // Note: Since bulkPredictions doesn't store formData for each employee, we'll use the latest formData as a fallback for context.
                            // In a real application, the CSV data should be stored and accessed here.
                            const { JobSatisfaction, WorkLifeBalance, OverTime, YearsAtCompany, MonthlyIncome, JobRole, Department } = formData;
                            const attritionProb = (bulkPredictions.attrition[idx].AttritionRiskProbability * 100).toFixed(2);
                            const performanceRating = bulkPredictions.performance[idx].PerformanceRating;
                            let reason = "";
                            let action = "";
                            if (JobSatisfaction <= 3) {
                              reason = `low job satisfaction (${JobSatisfaction}/5) likely contributes to their desire to leave`;
                              action = `address job satisfaction through career development opportunities or role-specific feedback`;
                            } else if (WorkLifeBalance <= 3) {
                              reason = `poor work-life balance (${WorkLifeBalance}/5) may be causing burnout`;
                              action = `offer flexible working hours or remote work options`;
                            } else if (OverTime === "Yes") {
                              reason = `frequent overtime could be driving dissatisfaction`;
                              action = `reduce overtime demands or provide compensation for extra hours`;
                            } else {
                              reason = `their high performance (${performanceRating}/5) may attract external offers`;
                              action = `offer a promotion or salary increase to match market rates`;
                            }
                            return (
                              <li key={idx}>
                                Employee {idx + 1} ({JobRole} in {Department}): A top performer (Rating: {performanceRating}/5) with {YearsAtCompany} years tenure and ${MonthlyIncome} income is at high risk of leaving ({attritionProb}% probability). Likely reason: {reason}. Recommended action: {action} to retain this valuable asset.
                              </li>
                            );
                          })
                      : <li>No high-risk high performers detected.</li>}
                  </ul>
                  <h3>Poor Performers</h3>
                  <ul>
                    {bulkPredictions.performance
                      ? bulkPredictions.performance
                          .map((pred, idx) => ({ pred, idx }))
                          .filter(({ pred }) => pred.PerformanceRating < 3)
                          .map(({ idx }) => {
                            // Using formData as fallback for context, as above.
                            const { JobSatisfaction, EnvironmentSatisfaction, TrainingTimesLastYear, OverTime, JobRole, Department } = formData;
                            const performanceRating = bulkPredictions.performance[idx].PerformanceRating;
                            let reason = "";
                            let action = "";
                            if (JobSatisfaction <= 2) {
                              reason = `low job satisfaction (${JobSatisfaction}/5) suggests disengagement from their role`;
                              action = `conduct one-on-one meetings to understand their concerns and align their role with personal goals`;
                            } else if (EnvironmentSatisfaction <= 2) {
                              reason = `poor environment satisfaction (${EnvironmentSatisfaction}/5) indicates discomfort in their work setting`;
                              action = `improve workplace conditions or consider team/role reassignment`;
                            } else if (TrainingTimesLastYear <= 2) {
                              reason = `limited training (${TrainingTimesLastYear} sessions last year) may leave them unprepared`;
                              action = `enroll them in targeted training programs to enhance skills`;
                            } else if (OverTime === "Yes") {
                              reason = `excessive overtime could be impacting their productivity`;
                              action = `adjust workload to eliminate overtime and monitor stress levels`;
                            } else {
                              reason = `their performance (${performanceRating}/5) falls below expectations`;
                              action = `implement a performance improvement plan with clear milestones`;
                            }
                            return (
                              <li key={idx}>
                                Employee {idx + 1} ({JobRole} in {Department}): Underperforming with a rating of {performanceRating}/5. Likely reason: {reason}. Recommended action: {action} to improve output or consider termination if no progress is made.
                              </li>
                            );
                          })
                      : <li>No poor performers detected.</li>}
                  </ul>
                </div>
                <div className="bulk-actions">
                  <Button onClick={exportBulkToExcel}><FaFileExcel /> Excel</Button>
                  <Button onClick={exportSummaryReport}><FaFilePdf /> PDF</Button>
                </div>
              </motion.div>
            )}
          </>
        )}

        {tab === "analytics" && (
          <motion.div className="analytics-card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}>
            <h2><FaChartLine /> Analytics Dashboard</h2>
            <div className="plot-grid">
              <div className="plot-item">
                <Bar data={getAnalyticsPerformanceBar()} options={{ responsive: true, plugins: { title: { display: true, text: "Performance Distribution" } } }} />
              </div>
              <div className="plot-item">
                <Doughnut data={getAnalyticsJobSatisfactionDoughnut()} options={{ responsive: true, plugins: { title: { display: true, text: "Job Satisfaction" } } }} />
              </div>
              <div className="plot-item">
                <Radar data={getAnalyticsWorkLifeBalanceRadar()} options={{ responsive: true, plugins: { title: { display: true, text: "Work-Life Balance" } } }} />
              </div>
              <div className="plot-item">
                <Pie data={getAnalyticsAttritionPie()} options={{ responsive: true, plugins: { title: { display: true, text: "Attrition Risk" } } }} />
              </div>
              <div className="plot-item">
                <Line data={getAnalyticsRetentionLine()} options={{ responsive: true, plugins: { title: { display: true, text: "Retention Risk Trend" } } }} />
              </div>
              <div className="plot-item">
                <Scatter data={getAnalyticsEngagementScatter()} options={{ responsive: true, plugins: { title: { display: true, text: "Engagement vs Performance" } } }} />
              </div>
            </div>
            <div className="employee-list">
              <h3>Employees Likely to Leave</h3>
              <ul>
                {predictionHistory.length > 0 ? predictionHistory.flatMap((entry, i) =>
                  entry.bulkData?.attrition && entry.bulkData?.performance
                    ? entry.bulkData.attrition
                        .map((pred, idx) => ({ pred, idx, perf: entry.bulkData.performance[idx]?.PerformanceRating }))
                        .filter(({ pred, perf }) => pred.AttritionRisk === 1 && perf >= 4)
                        .map(({ idx }) => {
                          const { JobSatisfaction, WorkLifeBalance, OverTime, YearsAtCompany, MonthlyIncome, JobRole, Department } = entry.formData || formData;
                          const attritionProb = (entry.bulkData.attrition[idx].AttritionRiskProbability * 100).toFixed(2);
                          const performanceRating = entry.bulkData.performance[idx].PerformanceRating;
                          let reason = "";
                          let action = "";
                          if (YearsAtCompany >= 10) {
                            reason = `long tenure (${YearsAtCompany} years) suggests they may seek new challenges`;
                            action = `offer a promotion or leadership role to re-engage them`;
                          } else if (MonthlyIncome < 5000) {
                            reason = `relatively low income ($${MonthlyIncome}) may drive them to competitors`;
                            action = `review their compensation to align with industry standards`;
                          } else if (JobSatisfaction <= 3) {
                            reason = `low job satisfaction (${JobSatisfaction}/5) indicates disengagement`;
                            action = `provide mentorship or project variety to boost motivation`;
                          } else {
                            reason = `high performance (${performanceRating}/5) makes them attractive to other employers`;
                            action = `recognize their contributions with bonuses or public acknowledgment`;
                          }
                          return (
                            <li key={`${i}-${idx}`}>
                              Bulk Employee {idx + 1} (Prediction {i + 1}, {entry.timestamp}): {JobRole} in {Department} with {performanceRating}/5 performance and {YearsAtCompany} years tenure is at risk ({attritionProb}%). Reason: {reason}. Action: {action} to prevent turnover.
                            </li>
                          );
                        })
                    : entry.predictions?.attrition.AttritionRisk === 1 && entry.predictions.performance.PerformanceRating >= 4
                    ? [{
                        idx: i,
                        pred: entry.predictions.attrition,
                        perf: entry.predictions.performance.PerformanceRating
                      }].map(({ idx, pred, perf }) => {
                        const { JobSatisfaction, WorkLifeBalance, OverTime, YearsAtCompany, MonthlyIncome, JobRole, Department } = entry.formData || formData;
                        const attritionProb = (pred.AttritionRiskProbability * 100).toFixed(2);
                        let reason = "";
                        let action = "";
                        if (WorkLifeBalance <= 2) {
                          reason = `poor work-life balance (${WorkLifeBalance}/5) may cause burnout`;
                          action = `implement flexible schedules or wellness programs`;
                        } else if (OverTime === "Yes") {
                          reason = `overtime demands could reduce their commitment`;
                          action = `limit overtime and ensure adequate rest periods`;
                        } else {
                          reason = `their high performance (${perf}/5) attracts external opportunities`;
                          action = `offer retention bonuses or career advancement paths`;
                        }
                        return (
                          <li key={idx}>
                            Individual Prediction {idx + 1} ({entry.timestamp}): {JobRole} in {Department} with {perf}/5 performance and ${MonthlyIncome} income is at risk ({attritionProb}%). Reason: {reason}. Action: {action} to retain talent.
                          </li>
                        );
                      })
                    : []
                ) : <li>No data available.</li>}
              </ul>
              <h3>Poor Performers</h3>
              <ul>
                {predictionHistory.length > 0 ? predictionHistory.flatMap((entry, i) =>
                  entry.bulkData?.performance
                    ? entry.bulkData.performance
                        .map((pred, idx) => ({ pred, idx }))
                        .filter(({ pred }) => pred.PerformanceRating < 3)
                        .map(({ idx }) => {
                          const { JobSatisfaction, EnvironmentSatisfaction, TrainingTimesLastYear, OverTime, JobRole, Department } = entry.formData || formData;
                          const performanceRating = entry.bulkData.performance[idx].PerformanceRating;
                          let reason = "";
                          let action = "";
                          if (TrainingTimesLastYear <= 1) {
                            reason = `minimal training (${TrainingTimesLastYear} sessions) limits their effectiveness`;
                            action = `provide intensive skill-building workshops`;
                          } else if (EnvironmentSatisfaction <= 2) {
                            reason = `low environment satisfaction (${EnvironmentSatisfaction}/5) suggests an unsuitable work setting`;
                            action = `relocate them to a different team or office`;
                          } else if (JobSatisfaction <= 2) {
                            reason = `low job satisfaction (${JobSatisfaction}/5) reduces motivation`;
                            action = `explore their career aspirations and align tasks accordingly`;
                          } else {
                            reason = `performance (${performanceRating}/5) is consistently below expectations`;
                            action = `initiate a formal performance review with clear improvement targets`;
                          }
                          return (
                            <li key={`${i}-${idx}`}>
                              Bulk Employee {idx + 1} (Prediction {i + 1}, {entry.timestamp}): {JobRole} in {Department} with {performanceRating}/5 rating. Reason: {reason}. Action: {action} or consider termination if no improvement.
                            </li>
                          );
                        })
                    : entry.predictions?.performance.PerformanceRating < 3
                    ? [{
                        idx: i,
                        pred: entry.predictions.performance
                      }].map(({ idx, pred }) => {
                        const { JobSatisfaction, EnvironmentSatisfaction, TrainingTimesLastYear, OverTime, JobRole, Department } = entry.formData || formData;
                        const performanceRating = pred.PerformanceRating;
                        let reason = "";
                        let action = "";
                        if (OverTime === "Yes") {
                          reason = `overtime may overwhelm their capacity`;
                          action = `reduce workload and prioritize key tasks`;
                        } else if (JobSatisfaction <= 2) {
                          reason = `low job satisfaction (${JobSatisfaction}/5) hinders performance`;
                          action = `offer coaching to address dissatisfaction`;
                        } else {
                          reason = `performance (${performanceRating}/5) does not meet standards`;
                          action = `set up a performance improvement plan with regular check-ins`;
                        }
                        return (
                          <li key={idx}>
                            Individual Prediction {idx + 1} ({entry.timestamp}): {JobRole} in {Department} with {performanceRating}/5 rating. Reason: {reason}. Action: {action} or evaluate role fit.
                          </li>
                        );
                      })
                    : []
                ) : <li>No data available.</li>}
              </ul>
            </div>
          </motion.div>
        )}
      </main>
    </div>
  );
};

export default EmployeeForm;

import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Home from "./pages/Home";
import QuizDetail from "./pages/QuizDetail";
import { AddQuiz, EditQuiz } from "./pages/AddEditQuiz"
import Upload from "./pages/Upload";
import Register from "./pages/Register"; 
import Login from "./pages/Login";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/home" element={<Home />} />
        <Route path="/quiz/:quiz_name" element={<QuizDetail />} />
        <Route path="/add-quiz" element={<AddQuiz />} />
        <Route path="/edit/:quiz_name" element={<EditQuiz />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/" element={<Register />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Routes>
    </Router>
  );
}

export default App;

import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import axios from "axios";

const AddQuiz = () => {
  const [quizName, setQuizName] = useState("");
  const [questions, setQuestions] = useState([
    { question: "", type: "multiple", options: ["", "", "", ""], answer: "" }
  ]);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleQuestionChange = (index, field, value) => {
    const updatedQuestions = [...questions];

    if (field === "question") {
      updatedQuestions[index].question = value;
    } else if (field === "type") {
      updatedQuestions[index].type = value;
      updatedQuestions[index].options = value === "true/false" ? ["True", "False"] : ["", "", "", ""];
      updatedQuestions[index].answer = "";
    } else if (field === "answer") {
      updatedQuestions[index].answer = value;
    } else {
      updatedQuestions[index].options[field] = value;
    }
    setQuestions(updatedQuestions);
  };

  const handleAddQuestion = () => {
    setQuestions([...questions, { question: "", type: "multiple", options: ["", "", "", ""], answer: "" }]);
  };

  const handleRemoveQuestion = (index) => {
    const updatedQuestions = questions.filter((_, i) => i !== index);
    setQuestions(updatedQuestions);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        setError("Bạn cần đăng nhập để thêm quiz.");
        return;
      }

      await axios.post(
        "http://localhost:8000/api/quizzes", 
        { quiz_name: quizName, questions },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      navigate("/home");
    } catch (err) {
      setError("Không thể thêm quiz. Vui lòng thử lại.");
    }
  };

  return (
    <div className="flex flex-col items-center min-h-screen bg-gradient-to-r from-blue-400 to-purple-500 p-6">
      <h1 className="text-4xl font-bold mb-6">Thêm Quiz</h1>
      <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow w-full max-w-3xl">
        <div className="mb-4">
          <label className="block text-lg font-semibold mb-2">Tên Quiz</label>
          <input
            type="text"
            value={quizName}
            onChange={(e) => setQuizName(e.target.value)}
            className="w-full p-2 border rounded"
            required
          />
        </div>
        {questions.map((q, index) => (
          <div key={index} className="mb-6 border p-4 rounded">
            <label className="block text-lg font-semibold mb-2">Câu hỏi {index + 1}</label>
            <input
              type="text"
              value={q.question}
              onChange={(e) => handleQuestionChange(index, "question", e.target.value)}
              className="w-full p-2 border rounded mb-4"
              required
            />
            <div className="mb-4">
              <label className="block text-lg font-semibold mb-2">Loại câu hỏi</label>
              <select
                value={q.type}
                onChange={(e) => handleQuestionChange(index, "type", e.target.value)}
                className="w-full p-2 border rounded"
              >
                <option value="multiple">Multiple Choice</option>
                <option value="true/false">True/False</option>
              </select>
            </div>
            {q.type === "multiple" &&
              q.options.map((opt, idx) => (
                <div key={idx} className="mb-2">
                  <label>Tuỳ chọn {idx + 1}</label>
                  <input
                    type="text"
                    value={opt}
                    onChange={(e) => handleQuestionChange(index, idx, e.target.value)}
                    className="w-full p-2 border rounded"
                    required
                  />
                </div>
              ))}
            <div className="mt-4">
              <label>Đáp án (Nhập True/False hoặc 0 - 3 nếu là Multiple Choice)</label>
              <input
                type="text"
                value={q.answer}
                onChange={(e) => handleQuestionChange(index, "answer", e.target.value)}
                className="w-full p-2 border rounded"
                required
              />
            </div>
            <button
              type="button"
              onClick={() => handleRemoveQuestion(index)}
              className="mt-4 bg-red-500 text-white py-2 px-4 rounded hover:bg-red-700"
            >
              Xóa câu hỏi
            </button>
          </div>
        ))}
        <button
          type="button"
          onClick={handleAddQuestion}
          className="bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-700 mb-4"
        >
          Thêm câu hỏi mới
        </button>
        {error && <p className="text-red-500 mb-4">{error}</p>}
        <button
          type="submit"
          className="bg-green-500 text-white py-2 px-4 rounded hover:bg-green-700"
        >
          Lưu Quiz
        </button>
      </form>
      <button
          onClick={() => (window.location.href = "/home")}
          className="mt-2 bg-gray-500 text-white py-2 px-4 rounded hover:bg-gray-700 transition"
        >
          Quay lại Home
        </button>
    </div>
  );
};

const EditQuiz = () => {
  const { quiz_name } = useParams();
  const [quiz, setQuiz] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchQuiz = async () => {
      const token = localStorage.getItem('token'); // Lấy token từ localStorage

      try {
        const response = await axios.get(`http://localhost:8000/api/quizzes/${quiz_name}`, {
          headers: {
            Authorization: `Bearer ${token}`, // Gửi token trong header
          },
        });
        setQuiz(response.data);
      } catch (err) {
        setError("Không thể tải chi tiết quiz.");
      }
    };

    if (quiz_name) {
      fetchQuiz();
    }
  }, [quiz_name]);

  const handleQuestionChange = (index, field, value) => {
    const updatedQuestions = [...quiz.questions];
    if (field === "question") {
      updatedQuestions[index].question = value;
    } else if (field === "answer") {
      updatedQuestions[index].answer = value;
    } else {
      updatedQuestions[index].options[field] = value;
    }
    setQuiz({ ...quiz, questions: updatedQuestions });
  };

  const handleSave = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('token'); // Lấy token từ localStorage

    try {
      await axios.put(`http://localhost:8000/api/quizzes/${quiz_name}`, quiz, {
        headers: {
          Authorization: `Bearer ${token}`, // Gửi token trong header
        },
      });
      navigate("/home");
    } catch (err) {
      setError("Không thể cập nhật quiz. Vui lòng thử lại.");
    }
  };

  if (error) {
    return <p className="text-red-500">{error}</p>;
  }

  if (!quiz) {
    return <p>Đang tải chi tiết quiz...</p>;
  }

  return (
    <div className="flex flex-col items-center min-h-screen bg-gradient-to-r from-blue-400 to-purple-500 p-6">
      <h1 className="text-4xl font-bold mb-6">Chỉnh sửa Quiz</h1>
      <form onSubmit={handleSave} className="bg-white p-6 rounded-lg shadow w-full max-w-3xl">
        <div className="mb-4">
          <label className="block text-lg font-semibold mb-2">Tên Quiz</label>
          <input
            type="text"
            value={quiz.quiz_name}
            onChange={(e) => setQuiz({ ...quiz, quiz_name: e.target.value })}
            className="w-full p-2 border rounded"
            required
          />
        </div>
        {quiz.questions.map((q, index) => (
          <div key={index} className="mb-6 border p-4 rounded">
            <label className="block text-lg font-semibold mb-2">Câu hỏi {index + 1}</label>
            <input
              type="text"
              value={q.question}
              onChange={(e) => handleQuestionChange(index, "question", e.target.value)}
              className="w-full p-2 border rounded mb-4"
              required
            />
            {q.options.map((opt, idx) => (
              <div key={idx} className="mb-2">
                <label>Tuỳ chọn {idx + 1}</label>
                <input
                  type="text"
                  value={opt}
                  onChange={(e) => handleQuestionChange(index, idx, e.target.value)}
                  className="w-full p-2 border rounded"
                  required
                />
              </div>
            ))}
            <div className="mt-4">
              <label>Đáp án (Nhập True/False hoặc 0 - 3 nếu là Multiple Choice)</label>
              <input
                type="text"
                value={q.answer}
                onChange={(e) => handleQuestionChange(index, "answer", e.target.value)}
                className="w-full p-2 border rounded"
                required
              />
            </div>
          </div>
        ))}
        {error && <p className="text-red-500 mb-4">{error}</p>}
        <button
          type="submit"
          className="bg-green-500 text-white py-2 px-4 rounded hover:bg-green-700"
        >
          Lưu Quiz
        </button>
      </form>
      <button
          onClick={() => (window.location.href = "/home")}
          className="mt-2 bg-gray-500 text-white py-2 px-4 rounded hover:bg-gray-700 transition"
        >
          Quay lại Home
        </button>
    </div>
  );
};

export { AddQuiz, EditQuiz };

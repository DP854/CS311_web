import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";

const QuizDetail = () => {
  const { quiz_name } = useParams();
  const [quiz, setQuiz] = useState(null);
  const [error, setError] = useState(null);
  const [answers, setAnswers] = useState([]);
  const [result, setResult] = useState(null);

  useEffect(() => {
    const fetchQuiz = async () => {
      try {
        const token = localStorage.getItem("token");

        if (!token) {
          setError("Vui lòng đăng nhập.");
          return;
        }

        const response = await axios.get(`http://localhost:8000/api/quizzes/${quiz_name}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setQuiz(response.data);
        setAnswers(Array(response.data.questions.length).fill(""));
      } catch (err) {
        setError("Không thể tải chi tiết quiz.");
      }
    };

    if (quiz_name) {
      fetchQuiz();
    }
  }, [quiz_name]);

  const handleAnswerChange = (index, value) => {
    const newAnswers = [...answers];
    newAnswers[index] = value;
    setAnswers(newAnswers);
  };

  const submitQuiz = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.post(
        `http://localhost:8000/api/quizzes/${quiz_name}/attempt`,
        answers,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      setResult(response.data);
    } catch (err) {
      setError("Không thể gửi bài làm.");
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
      <h1 className="text-4xl font-bold mb-6">{quiz.quiz_name}</h1>
      <div className="bg-white p-6 rounded-lg shadow w-full max-w-3xl">
        <h2 className="text-2xl font-bold mb-4">{quiz.quiz_name}</h2>
        <ul className="space-y-4">
          {quiz.questions.map((question, index) => (
            <li key={index} className="p-4 border rounded-lg bg-gray-50">
              <h3 className="font-semibold">Câu {index + 1}. {question.question}</h3>
              <div className="mt-2">
                {question.options.map((option, idx) => (
                  <label key={idx} className="block">
                    <input
                      type="radio"
                      name={`question-${index}`}
                      value={option}
                      onChange={() => handleAnswerChange(index, option)}
                    />
                    {option}
                  </label>
                ))}
              </div>
            </li>
          ))}
        </ul>
        <button
          onClick={submitQuiz}
          className="mt-6 bg-green-500 text-white py-2 px-4 rounded hover:bg-green-700 transition"
        >
          Nộp bài
        </button>
        {result && (
          <div className="mt-6 bg-gray-100 p-4 rounded">
            <p className="font-bold">Kết quả: {result.score}/{result.total}</p>
            <p>Đáp án đúng: {result.answers.join(", ")}</p>
          </div>
        )}
        <Link to="/home" className="mt-6 inline-block bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-700 transition">
          Quay lại
        </Link>
      </div>
    </div>
  );
};

export default QuizDetail;

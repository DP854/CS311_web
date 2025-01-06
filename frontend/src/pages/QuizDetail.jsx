import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";

const QuizDetail = () => {
  const { quiz_name } = useParams();
  const [quiz, setQuiz] = useState(null);
  const [error, setError] = useState(null);
  const [answers, setAnswers] = useState([]);
  const [result, setResult] = useState(null);
  const [submitted, setSubmitted] = useState(false);
  console.log("🚀 ~ QuizDetail ~ answers:", answers)
  console.log("🚀 ~ QuizDetail ~ result:", result)

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

  const handleAnswerChange = (index, value, idx) => {
    const newAnswers = [...answers];
    if (value === 'True' || value === 'False') {
      newAnswers[index] = value;
    } else {
      newAnswers[index] = idx.toString();
    }
    setAnswers(newAnswers);
  };

  const isAnswerCorrect = (questionIndex) => {
    if (!result || !result.answers) return null;
    const userAnswer = answers[questionIndex];
    const correctAnswer = result.answers[questionIndex];

    // Handle boolean answers
    if (typeof correctAnswer === 'boolean') {
      return userAnswer === (correctAnswer ? 'True' : 'False');
    }
    // Handle numeric answers
    return userAnswer === correctAnswer.toString();
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
      setSubmitted(true);
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
      <h1 className="text-4xl font-bold mb-6 text-white">{quiz.quiz_name}</h1>
      <div className="bg-white p-6 rounded-lg shadow w-full max-w-3xl">
        <ul className="space-y-4">
          {quiz.questions.map((question, index) => (
            <li key={index} className="p-4 border rounded-lg bg-gray-50">
              <h3 className="font-semibold">Câu {index + 1}. {question.question}</h3>
              <div className="mt-2 space-y-2">
                {question.options.map((option, idx) => {
                  const isCorrect = submitted && isAnswerCorrect(index);
                  const isSelected = answers[index] === (option === 'True' || option === 'False' ? option : idx.toString());

                  return (
                    <label
                      key={idx}
                      // ${submitted  && (
                      //   isSelected && isCorrect ? 'text-green-600' : (
                      //     !isSelected && isCorrect ? 'text-green-600' : (
                      //       isSelected && !isCorrect ? 'text-red-600': 'text-black'
                      //     )
                      //   )
                      // )}
                      className={`block p-2 rounded cursor-pointer transition-colors
                        ${isSelected && submitted ? (isCorrect ? 'text-green-600' : 'text-red-600') : ''}
                        ${isSelected ? 'bg-gray-100' : 'hover:bg-gray-100'}
                        
                        `}
                    >
                      <input
                        type="radio"
                        name={`question-${index}`}
                        value={option}
                        onChange={() => handleAnswerChange(index, option, idx)}
                        disabled={submitted}
                        className="mr-2"
                      />
                      <span>{option}</span>
                    </label>
                  );
                })}
                {submitted ? (
                  <p className="text-white font-semibold shadow-xl bg-green-600 inline-block p-2 rounded-md ">
                    Correct Answer:&nbsp; 
                    {result.answers[index] === "True" || result.answers[index] === 'False' ? result.answers[index] : (
                      question.options[parseInt(result.answers[index])]
                    )}
                  </p>
                ) : (
                  ''
                )}
              </div>
            </li>
          ))}
        </ul>

        {!submitted ? (
          <button
            onClick={submitQuiz}
            className="mt-6 bg-green-500 text-white py-2 px-4 rounded hover:bg-green-600 transition"
          >
            Nộp bài
          </button>
        ) : (
          <div className="mt-6 bg-gray-100 p-4 rounded">
            <p className="font-bold text-lg mb-2">
              Kết quả: <span className="text-blue-600">{result.score}/{result.total}</span>
            </p>
          </div>
        )}

        <Link
          to="/home"
          className="mt-4 inline-block bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600 transition"
        >
          Quay lại
        </Link>
      </div>
    </div>
  );
};

export default QuizDetail;
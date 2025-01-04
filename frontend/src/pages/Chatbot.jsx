import React, { useState } from "react";
import axios from "axios";

const Chatbot = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await axios.post(
        "http://localhost:8000/chat",
        { query: input }
      );

      const botMessage = { sender: "bot", text: response.data.response };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Error details:", error.response ? error.response.data : error.message);
      
      const errorMessage = { sender: "bot", text: "Có lỗi xảy ra. Vui lòng thử lại!" };
      setMessages((prev) => [...prev, errorMessage]);
    }

    setInput("");
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-100">
      <div className="w-full max-w-lg p-6 bg-white rounded-lg shadow-lg">
        <div className="h-96 overflow-y-auto mb-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`my-2 p-3 rounded-lg ${
                message.sender === "user"
                  ? "bg-blue-500 text-white self-end"
                  : "bg-gray-200 text-gray-800 self-start"
              }`}
            >
              {message.text}
            </div>
          ))}
        </div>
        <div className="flex">
          <input
            type="text"
            placeholder="Nhập câu hỏi của bạn..."
            className="flex-grow p-2 border rounded-l-lg focus:outline-none"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
          />
          <button
            onClick={handleSendMessage}
            className="px-4 py-2 bg-blue-500 text-white rounded-r-lg hover:bg-blue-600"
          >
            Gửi
          </button>
        </div>
      </div>
      <button
          onClick={() => (window.location.href = "/home")}
          className="mt-2 bg-gray-500 text-white py-2 px-4 rounded hover:bg-gray-700 transition"
        >
          Quay lại Home
        </button>
    </div>
  );
};

export default Chatbot;

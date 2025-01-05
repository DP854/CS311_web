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
      const response = await axios.post("http://localhost:8000/chat", { query: input });

      const { response: botResponse, search_results } = response.data;

      const botMessage = { sender: "bot", text: botResponse };
      setMessages((prev) => [...prev, botMessage]);

      // Log or store search_results if needed
      console.log("Search Results:", search_results);
    } catch (error) {
      console.error("Error details:", error.response ? error.response.data : error.message);

      const errorMessage = { sender: "bot", text: "Có lỗi xảy ra. Vui lòng thử lại!" };
      setMessages((prev) => [...prev, errorMessage]);
    }

    setInput("");
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gradient-to-t from-blue-100 to-blue-200">
      <div className="w-full max-w-lg p-6 bg-white rounded-lg shadow-lg border border-gray-200">
        <div className="h-96 overflow-y-auto mb-4 p-4 space-y-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg max-w-[80%] ${message.sender === "user"
                ? "bg-blue-500 text-white self-end ml-auto"
                : "bg-gray-200 text-gray-800 self-start mr-auto"
                }`}
                dangerouslySetInnerHTML={{
                  __html: message.text
                    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>") // Thay **text** thành <strong>text</strong>
                    .replace(/\*(.+?)\*/g, "<em>$1</em>") // Thay *text* thành <em>text</em>
                    .replace(/^\*\s(.+)/gm, "• $1") // Thay dấu * đầu dòng thành dấu gạch đầu dòng
                    .replace(/\n/g, "<br />") // Thay ký tự xuống dòng thành <br />
                }}>
                {/*  >{message.text} */}
            </div>  
          ))}
        </div>
        <div className="flex space-x-2 mt-4">
          <input
            type="text"
            placeholder="Nhập câu hỏi của bạn..."
            className="flex-grow p-3 border rounded-l-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
          />
          <button
            onClick={handleSendMessage}
            className="px-6 py-3 bg-blue-500 text-white rounded-r-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Gửi
          </button>
        </div>
      </div>
      <button
        onClick={() => (window.location.href = "/home")}
        className="mt-4 bg-gray-500 text-white py-2 px-4 rounded-lg hover:bg-gray-600 transition"
      >
        Quay lại Home
      </button>
    </div>
  );
};

export default Chatbot;

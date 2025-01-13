import React, { useState } from "react";
import axios from "axios";

const Upload = ({ onUploadSuccess }) => {
  const [pdfFile, setPdfFile] = useState(null);
  const [filename, setFilename] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    setPdfFile(file);
    setFilename(file.name);
  };

  const handleSubmit = async (e, action) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", pdfFile);
    formData.append("filename", filename);

    const token = localStorage.getItem('token');

    try {
      const uploadResponse = await axios.post("http://localhost:8000/upload", formData, {
        headers: { 
          "Content-Type": "multipart/form-data",
          Authorization: `Bearer ${token}`, 
        },
      });

      if (uploadResponse.data.filename) {
        if(action === "createQuiz") {
          const processResponse = await axios.post("http://localhost:8000/process-pdf-to-quiz", formData, {
            headers: { 
              "Content-Type": "multipart/form-data",
              Authorization: `Bearer ${token}`,
            },
          });
          if (processResponse) {
            alert("Tạo quiz thành công!");
            onUploadSuccess();
          }
        } else if (action === "chatWithBot") {
            const chatResponse = await axios.post("http://localhost:8000/process-pdf-to-chat", formData, {
              headers: { 
                "Content-Type": "multipart/form-data",
                Authorization: `Bearer ${token}`,
              },
            });

            if(chatResponse) {
              alert("Lưu vào chat thành công!");
              onUploadSuccess();
          }
        }
      }
    } catch (err) {
      setError("Tải lên PDF không thành công. Vui lòng thử lại.");
    } finally {
      setLoading(false);
    }
  };

  return (
      <div className="text-center w-full max-w-lg bg-white p-8 rounded-xl">
        <h1 className="text-3xl font-bold mb-4">Tải lên PDF và tạo câu hỏi</h1>

        {pdfFile && (
          <div className="mb-4 text-left bg-gray-200 p-4 rounded shadow">
            <h2 className="text-xl font-semibold">Thông tin file:</h2>
            <p><strong>Tên file:</strong> {filename}</p>
            <p><strong>Kích thước:</strong> {(pdfFile.size / 1024).toFixed(2)} KB</p>
            <iframe
              src={pdfFile ? URL.createObjectURL(pdfFile): ''}
              title="PDF Preview"
              className="w-full h-64 mt-4 border"
            ></iframe>
          </div>
        )}

        <form>
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="mb-4 p-2 border rounded"
            required
          />
          <div className="mb-4">
            {loading ? (
              <p>Đang xử lý...</p>
            ) : (
              <>
                <button
                  type="button"
                  onClick={(e) => handleSubmit(e, "createQuiz")}
                  className="bg-blue-500 text-white py-2 px-4 mt-6 mr-2 rounded hover:bg-blue-700 transition"
                >
                  Tạo câu hỏi
                </button>
                <button
                  type="button"
                  onClick={(e) => handleSubmit(e, "chatWithBot")}
                  className="bg-green-500 text-white py-2 px-4 mt-6 rounded hover:bg-green-700 transition"
                >
                  Lưu vào ChatPDF
                </button>
              </>
            )}
          </div>
        </form>
        {error && <p className="text-red-500">{error}</p>}
      </div>
  );
};

export default Upload;
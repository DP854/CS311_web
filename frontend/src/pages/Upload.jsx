import React, { useState } from "react";
import axios from "axios";

const Upload = () => {
  const [pdfFile, setPdfFile] = useState(null);
  const [filename, setFilename] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    setPdfFile(file);
    setFilename(file.name);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", pdfFile);
    formData.append("filename", filename);

    const token = localStorage.getItem('token');

    try {
      const uploadResponse = await axios.post("http://localhost:8000/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      if (uploadResponse.data.filename) {
        const processResponse = await axios.post("http://localhost:8000/process-pdf", formData, {
          headers: { 
            "Content-Type": "multipart/form-data",
            Authorization: `Bearer ${token}`,
          },
        });

        if (processResponse.data) {
          alert("Tải lên và tạo quiz thành công!");
        }
      }
    } catch (err) {
      setError("Tải lên PDF không thành công. Vui lòng thử lại.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex justify-center items-center min-h-screen bg-blue-200">
      <div className="text-center w-full max-w-lg bg-white p-8 rounded-xl">
        <h1 className="text-3xl font-bold mb-4">Tải lên PDF và tạo câu hỏi</h1>

        {pdfFile && (
          <div className="mb-4 text-left bg-gray-200 p-4 rounded shadow">
            <h2 className="text-xl font-semibold">Thông tin file:</h2>
            <p><strong>Tên file:</strong> {filename}</p>
            <p><strong>Kích thước:</strong> {(pdfFile.size / 1024).toFixed(2)} KB</p>
            <iframe
              src={URL.createObjectURL(pdfFile)}
              title="PDF Preview"
              className="w-full h-64 mt-4 border"
            ></iframe>
          </div>
        )}

        <form onSubmit={handleUpload}>
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="mb-4 p-2 border rounded"
            required
          />
          <div className="mb-4">
            {loading ? (
              <p>Đang tạo...</p>
            ) : (
              <button
                type="submit"
                className="bg-blue-500 text-white py-2 px-4 mt-6 rounded hover:bg-blue-700 transition"
              >
                Tạo câu hỏi
              </button>
            )}
          </div>
        </form>
        {error && <p className="text-red-500">{error}</p>}

        <button
          onClick={() => (window.location.href = "/home")}
          className="mt-2 bg-gray-500 text-white py-2 px-4 rounded hover:bg-gray-700 transition"
        >
          Quay lại Home
        </button>
      </div>
    </div>
  );
};

export default Upload;
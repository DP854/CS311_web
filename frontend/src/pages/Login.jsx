import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const Login = () => {
  const [formData, setFormData] = useState({
    username: "",
    password: "",
  });
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.username || !formData.password) {
      setError("Vui lòng điền đầy đủ thông tin.");
      return;
    }
    try {
      const response = await axios.post("http://localhost:8000/api/login", formData);
      const token = response.data.token;
      localStorage.setItem("token", token); // Lưu token
      navigate("/home");
    } catch (err) {
      if (!err.response) {
        setError("Không thể kết nối tới server. Vui lòng thử lại sau.");
      } else {
        setError(err.response?.data?.message || "Đăng nhập thất bại. Vui lòng thử lại.");
      }
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-r from-blue-400 to-purple-500">
      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md">
        <h2 className="text-3xl font-bold mb-6 text-center text-gray-700">Đăng Nhập</h2>
        {error && <p className="text-red-500 mb-4 text-center">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="username" className="block font-medium text-gray-700">
              Tên người dùng
            </label>
            <input
              type="text"
              name="username"
              id="username"
              value={formData.username}
              onChange={handleChange}
              className="w-full mt-1 p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label htmlFor="password" className="block font-medium text-gray-700">
              Mật khẩu
            </label>
            <input
              type="password"
              name="password"
              id="password"
              value={formData.password}
              onChange={handleChange}
              className="w-full mt-1 p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
          >
            Đăng Nhập
          </button>
        </form>
        <p className="text-center text-gray-600 mt-6">
          Chưa có tài khoản?
          <span
            className="text-blue-600 font-semibold cursor-pointer hover:underline"
            onClick={() => navigate("/register")}
          >
            Đăng ký
          </span>
        </p>
      </div>
    </div>
  );
};

export default Login;

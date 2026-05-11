import axios, { AxiosError } from 'axios';

const axiosClient = axios.create({
  baseURL: "http://localhost:8080/api/",
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a response interceptor
axiosClient.interceptors.response.use(
  function (response) {
    // Any status code that lie within the range of 2xx cause this function to trigger
    // Do something with response data
    return response.data;
  },
  function (error) {
    // Any status codes that falls outside the range of 2xx cause this function to trigger
    // Do something with response error
    if (error.response?.status === 401) {
        console.log(error)
    }
    return Promise.reject(error);
  },
);

export default axiosClient;
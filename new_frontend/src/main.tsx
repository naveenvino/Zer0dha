import React from "react";
import ReactDOM from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import Layout from "@/components/Layout";
import "./index.css";

// Import your page components here
import Dashboard from "@/pages/Dashboard";
import Orders from "@/pages/Orders";
import Holdings from "@/pages/Holdings";
import Watchlist from "@/pages/Watchlist";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: "orders", element: <Orders /> },
      { path: "holdings", element: <Holdings /> },
      { path: "watchlist", element: <Watchlist /> },
    ],
  },
]);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
);
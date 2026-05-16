export default function FeedbackPage() {
  return (
    <div className="flex min-h-screen bg-gray-100 font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-[#06152b] text-white p-6">
        <h1 className="text-2xl font-bold text-orange-500 mb-10">
          FireFusion
        </h1>

        <nav className="space-y-3">
          <div className="p-3 rounded-lg hover:bg-slate-700 cursor-pointer">
            Dashboard
          </div>

          <div className="p-3 rounded-lg hover:bg-slate-700 cursor-pointer">
            Bushfire Map
          </div>

          <div className="p-3 rounded-lg hover:bg-slate-700 cursor-pointer">
            Misinformation Review
          </div>

          <div className="p-3 rounded-lg bg-orange-500 cursor-pointer font-semibold">
            Feedback
          </div>

          <div className="p-3 rounded-lg hover:bg-slate-700 cursor-pointer">
            Settings
          </div>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-10">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-800">Feedback</h1>
          <p className="text-gray-500 mt-2">
            Share your thoughts and help improve the FireFusion platform.
          </p>
        </div>

        {/* Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Feedback Form */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h2 className="text-2xl font-semibold text-gray-800 mb-6">
              Submit Feedback
            </h2>

            <div className="space-y-5">
              <div>
                <label className="block mb-2 font-medium text-gray-700">
                  Feedback Type
                </label>

                <select className="w-full border border-gray-300 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-orange-400">
                  <option>General Feedback</option>
                  <option>Bug Report</option>
                  <option>Feature Request</option>
                  <option>UI Improvement</option>
                </select>
              </div>

              <div>
                <label className="block mb-2 font-medium text-gray-700">
                  Title
                </label>

                <input
                  type="text"
                  placeholder="Enter feedback title"
                  className="w-full border border-gray-300 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-orange-400"
                />
              </div>

              <div>
                <label className="block mb-2 font-medium text-gray-700">
                  Description
                </label>

                <textarea
                  rows="6"
                  placeholder="Write your feedback here..."
                  className="w-full border border-gray-300 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-orange-400"
                ></textarea>
              </div>

              <div>
                <label className="block mb-2 font-medium text-gray-700">
                  Rating
                </label>

                <div className="flex gap-2 text-2xl text-yellow-400">
                  ★ ★ ★ ★ ★
                </div>
              </div>

              <button className="w-full bg-orange-500 hover:bg-orange-600 transition-all text-white py-3 rounded-lg font-semibold text-lg">
                Submit Feedback
              </button>
            </div>
          </div>

          {/* Feedback History */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h2 className="text-2xl font-semibold text-gray-800 mb-6">
              Feedback History
            </h2>

            <div className="space-y-4">
              {/* Feedback Card 1 */}
              <div className="border border-gray-200 rounded-xl p-5 hover:shadow-md transition-all">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-semibold text-gray-800">
                    Improve Bushfire Alerts
                  </h3>

                  <span className="bg-yellow-100 text-yellow-700 text-sm px-3 py-1 rounded-full font-medium">
                    Pending
                  </span>
                </div>

                <p className="text-sm text-orange-500 font-medium mb-2">
                  Feature Request
                </p>

                <p className="text-gray-600 text-sm mb-3">
                  Add push notifications for high-risk bushfire zones and live
                  emergency updates.
                </p>

                <p className="text-xs text-gray-400">12 May 2026</p>
              </div>

              {/* Feedback Card 2 */}
              <div className="border border-gray-200 rounded-xl p-5 hover:shadow-md transition-all">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-semibold text-gray-800">
                    Dashboard Loading Bug
                  </h3>

                  <span className="bg-blue-100 text-blue-700 text-sm px-3 py-1 rounded-full font-medium">
                    Reviewed
                  </span>
                </div>

                <p className="text-sm text-orange-500 font-medium mb-2">
                  Bug Report
                </p>

                <p className="text-gray-600 text-sm mb-3">
                  Analytics graphs sometimes fail to load properly after user
                  login.
                </p>

                <p className="text-xs text-gray-400">10 May 2026</p>
              </div>

              {/* Feedback Card 3 */}
              <div className="border border-gray-200 rounded-xl p-5 hover:shadow-md transition-all">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-semibold text-gray-800">
                    Better Mobile Layout
                  </h3>

                  <span className="bg-green-100 text-green-700 text-sm px-3 py-1 rounded-full font-medium">
                    Resolved
                  </span>
                </div>

                <p className="text-sm text-orange-500 font-medium mb-2">
                  UI Improvement
                </p>

                <p className="text-gray-600 text-sm mb-3">
                  Improve responsiveness of the sidebar and dashboard widgets on
                  mobile devices.
                </p>

                <p className="text-xs text-gray-400">8 May 2026</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

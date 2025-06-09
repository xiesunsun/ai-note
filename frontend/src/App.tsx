import React from 'react';

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            AI闪念笔记
          </h1>
          <p className="text-lg text-gray-600">
            让碎片化信息变成结构化知识
          </p>
        </header>
        
        <main className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">
              欢迎使用AI闪念笔记
            </h2>
            <p className="text-gray-600 mb-6">
              这是一个专为信息碎片化时代设计的智能笔记应用。
              支持即时记录、AI辅助标签、智能知识关联和记忆提醒功能。
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="p-4 border border-gray-200 rounded-lg">
                <h3 className="font-semibold text-gray-800 mb-2">即时记录</h3>
                <p className="text-sm text-gray-600">
                  简洁的界面，支持Markdown格式，快速记录您的想法
                </p>
              </div>
              
              <div className="p-4 border border-gray-200 rounded-lg">
                <h3 className="font-semibold text-gray-800 mb-2">AI辅助</h3>
                <p className="text-sm text-gray-600">
                  自动标签生成、内容润色，让您的笔记更加完善
                </p>
              </div>
              
              <div className="p-4 border border-gray-200 rounded-lg">
                <h3 className="font-semibold text-gray-800 mb-2">知识关联</h3>
                <p className="text-sm text-gray-600">
                  智能发现笔记间的关联，构建您的知识网络
                </p>
              </div>
            </div>
            
            <div className="mt-8 text-center">
              <button className="btn-primary mr-4">
                开始记录
              </button>
              <button className="btn-secondary">
                了解更多
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;

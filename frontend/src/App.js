import { useEffect, useState } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import MeetingRecorder from "./components/Meetings/MeetingRecorder";
import VoiceChat from "./components/Voice/VoiceChat";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Home = () => {
  const helloWorldApi = async () => {
    try {
      const response = await axios.get(`${API}/`);
      console.log(response.data.message);
    } catch (e) {
      console.error(e, `errored out requesting / api`);
    }
  };

  useEffect(() => {
    helloWorldApi();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Заголовок приложения */}
        <header className="text-center mb-8">
          <a
            className="inline-block mb-4"
            href="https://emergent.sh"
            target="_blank"
            rel="noopener noreferrer"
          >
            <img 
              src="https://avatars.githubusercontent.com/in/1201222?s=120&u=2686cf91179bbafbc7a71bfbc43004cf9ae1acea&v=4" 
              alt="Emergent Logo"
              className="w-20 h-20 rounded-full mx-auto"
            />
          </a>
          <h1 className="text-4xl font-bold text-gray-800 mb-2">🎤 AudioBot</h1>
          <p className="text-xl text-gray-600">Диктофон планерок и живой разговор с ИИ</p>
        </header>

        {/* Основные вкладки */}
        <Tabs defaultValue="meetings" className="w-full">
          <TabsList className="grid w-full grid-cols-2 mb-6">
            <TabsTrigger value="meetings" className="text-lg py-3">
              🎤 Диктофон Планерок
            </TabsTrigger>
            <TabsTrigger value="voice" className="text-lg py-3">
              💬 Живой Разговор
            </TabsTrigger>
          </TabsList>

          <TabsContent value="meetings" className="space-y-4">
            <MeetingRecorder />
          </TabsContent>

          <TabsContent value="voice" className="space-y-4">
            <VoiceChat />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />}>
            <Route index element={<Home />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;

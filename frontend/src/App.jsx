import { useCallback, useState } from "react";
import LoginPage from "./pages/LoginPage";
import ProfilePage from "./pages/ProfilePage";
import RegisterPage from "./pages/RegisterPage";
import RequestPage from "./pages/RequestPage";
import SearchPage from "./pages/SearchPage";
import { getStoredToken } from "./services/authService";

function App() {
  const [view, setView] = useState(getStoredToken() ? "profile" : "login");
  const [selectedVolunteer, setSelectedVolunteer] = useState(null);
  const [notice, setNotice] = useState("");
  const [noticeIsError, setNoticeIsError] = useState(false);

  const showLogin = useCallback(() => {
    setView("login");
  }, []);

  const showRegister = useCallback(() => {
    setNotice("");
    setNoticeIsError(false);
    setView("register");
  }, []);

  const handleRegistered = useCallback(() => {
    setNotice("Account created. You can log in now.");
    setNoticeIsError(false);
    setView("login");
  }, []);

  const handleLoggedIn = useCallback(() => {
    setNotice("");
    setNoticeIsError(false);
    setView("profile");
  }, []);

  const handleLoggedOut = useCallback((message) => {
    setNotice(message || "");
    setNoticeIsError(Boolean(message));
    setView("login");
  }, []);

  const showSearch = useCallback(() => {
    setNotice("");
    setNoticeIsError(false);
    setView("search");
  }, []);

  const showRequest = useCallback((volunteer) => {
    setSelectedVolunteer(volunteer);
    setNotice("");
    setNoticeIsError(false);
    setView("request");
  }, []);

  const showProfile = useCallback(() => {
    setNotice("");
    setNoticeIsError(false);
    setView("profile");
  }, []);

  return (
    <main>
      <header>
        <p className="brand">VolunteerConnect</p>
      </header>
      {notice ? (
        <p className={noticeIsError ? "error" : "notice"}>{notice}</p>
      ) : null}
      {view === "register" ? (
        <RegisterPage onRegistered={handleRegistered} onShowLogin={showLogin} />
      ) : null}
      {view === "login" ? (
        <LoginPage onLoggedIn={handleLoggedIn} onShowRegister={showRegister} />
      ) : null}
      {view === "profile" ? (
        <ProfilePage onLoggedOut={handleLoggedOut} onShowSearch={showSearch} />
      ) : null}
      {view === "search" ? (
        <SearchPage
          onLoggedOut={handleLoggedOut}
          onShowProfile={showProfile}
          onRequestVolunteer={showRequest}
        />
      ) : null}
      {view === "request" && selectedVolunteer ? (
        <RequestPage
          volunteer={selectedVolunteer}
          onLoggedOut={handleLoggedOut}
          onShowSearch={showSearch}
        />
      ) : null}
    </main>
  );
}

export default App;

import { useCallback, useState } from "react";
import LoginPage from "./pages/LoginPage";
import MyRequestsPage from "./pages/MyRequestsPage";
import ProfilePage from "./pages/ProfilePage";
import RegisterPage from "./pages/RegisterPage";
import RequestPage from "./pages/RequestPage";
import SearchPage from "./pages/SearchPage";
import { getStoredToken } from "./services/authService";

function App() {
  const [view, setView] = useState(getStoredToken() ? "profile" : "login");
  const [selectedVolunteer, setSelectedVolunteer] = useState(null);
  const [searchPrefill, setSearchPrefill] = useState(null);
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

  // A fresh search from the profile starts with empty filters.
  const showSearch = useCallback(() => {
    setSearchPrefill(null);
    setNotice("");
    setNoticeIsError(false);
    setView("search");
  }, []);

  // Going back from the request form keeps any prefilled filters.
  const returnToSearch = useCallback(() => {
    setNotice("");
    setNoticeIsError(false);
    setView("search");
  }, []);

  const showSearchAgain = useCallback((request) => {
    setSearchPrefill(request);
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

  const showRequests = useCallback(() => {
    setNotice("");
    setNoticeIsError(false);
    setView("requests");
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
        <ProfilePage
          onLoggedOut={handleLoggedOut}
          onShowSearch={showSearch}
          onShowRequests={showRequests}
        />
      ) : null}
      {view === "requests" ? (
        <MyRequestsPage
          onLoggedOut={handleLoggedOut}
          onShowProfile={showProfile}
          onSearchAgain={showSearchAgain}
        />
      ) : null}
      {view === "search" ? (
        <SearchPage
          prefill={searchPrefill}
          onLoggedOut={handleLoggedOut}
          onShowProfile={showProfile}
          onRequestVolunteer={showRequest}
        />
      ) : null}
      {view === "request" && selectedVolunteer ? (
        <RequestPage
          volunteer={selectedVolunteer}
          prefill={searchPrefill}
          onLoggedOut={handleLoggedOut}
          onShowSearch={returnToSearch}
          onShowRequests={showRequests}
        />
      ) : null}
    </main>
  );
}

export default App;

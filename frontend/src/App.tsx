import { ChakraProvider } from '@chakra-ui/react';
import { Provider } from 'react-redux';
import {
  BrowserRouter,
  Routes,
  Route,
} from 'react-router-dom';
import { store } from './store';
import { LoginPage } from './features/auth/LoginPage';
import { SignupPage } from './features/auth/SignupPage';
import { DashboardLayout } from './components/Layout/DashboardLayout';
import { NewsTasks } from './features/newsTasks/NewsTasks';
import NewsItemsPage from './features/newsItems/NewsItemsPage';
import { NewspaperPage } from './features/newspaper/NewspaperPage';
import { PrivateRoute } from './components/PrivateRoute';

function App() {
  return (
    <Provider store={store}>
      <ChakraProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route
              path="/"
              element={
                <PrivateRoute>
                  <DashboardLayout />
                </PrivateRoute>
              }
            >
              <Route path="tasks" element={<NewsTasks />} />
              <Route path="news-items" element={<NewsItemsPage />} />
              <Route path="newspaper/:taskId" element={<NewspaperPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ChakraProvider>
    </Provider>
  );
}

export default App;

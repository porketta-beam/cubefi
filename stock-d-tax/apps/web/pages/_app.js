import '../styles/global.css';
import Header from '../components/Header';
import FloatingChatbot from '../components/FloatingChatbot';

export default function App({ Component, pageProps }) {
  return (
    <>
      <Header />
      <Component {...pageProps} />
      <FloatingChatbot />
    </>
  );
} 
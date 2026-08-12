import { StrictMode } from 'react'; import { createRoot } from 'react-dom/client'; import App from './App'; import './styles.css'
const initialDemo = new URLSearchParams(window.location.search).has('demo')
createRoot(document.getElementById('root')!).render(<StrictMode><App initialDemo={initialDemo}/></StrictMode>)

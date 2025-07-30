// src/firebase.ts
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, GithubAuthProvider } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyAXe4wQxtJRLbzr9GrS-IKnSy8SvQacZKk",
  authDomain: "voxaide.firebaseapp.com",
  projectId: "voxaide",
  appId: "1:916913870162:web:469429eaf26ba8f98dd68b",
  storageBucket: "voxaide.firebasestorage.app",
  measurementId: "G-ZFVZ76KCJ8",
  messagingSenderId: "916913870162"
};

const app = initializeApp(firebaseConfig);

// Firebase services
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();
const githubProvider = new GithubAuthProvider();
const db = getFirestore(app);

// ✅ Export all together
export { auth, db, googleProvider, githubProvider };

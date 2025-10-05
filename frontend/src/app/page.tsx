'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// Animated Background Component
const AnimatedBackground = () => {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none">
      {/* Animated gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900" />
      
      {/* Floating particles */}
      {Array.from({ length: 50 }).map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-1 h-1 bg-blue-400 rounded-full opacity-30"
          animate={{
            x: [0, Math.random() * 100 - 50],
            y: [0, Math.random() * 100 - 50],
            scale: [0, 1, 0],
          }}
          transition={{
            duration: Math.random() * 10 + 10,
            repeat: Infinity,
            ease: "linear",
          }}
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
          }}
        />
      ))}
      
      {/* Grid pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="h-full w-full bg-[linear-gradient(rgba(59,130,246,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(59,130,246,0.1)_1px,transparent_1px)] bg-[size:50px_50px]" />
      </div>
    </div>
  );
};

// Glowing Button Component
const GlowButton = ({ children, onClick, className = "", variant = "primary" }: {
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
  variant?: "primary" | "secondary" | "accent";
}) => {
  const baseClasses = "relative px-8 py-4 rounded-lg font-semibold text-lg transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-opacity-50";
  
  const variants = {
    primary: "bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-500 hover:to-purple-500 focus:ring-blue-400 hover:shadow-[0_0_30px_rgba(59,130,246,0.6),0_0_60px_rgba(147,51,234,0.4)]",
    secondary: "bg-gradient-to-r from-slate-700 to-slate-800 text-blue-300 hover:from-slate-600 hover:to-slate-700 focus:ring-slate-400 hover:shadow-[0_0_30px_rgba(59,130,246,0.6),0_0_60px_rgba(147,51,234,0.4)]",
    accent: "bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-500 hover:to-pink-500 focus:ring-purple-400 hover:shadow-[0_0_30px_rgba(59,130,246,0.6),0_0_60px_rgba(147,51,234,0.4)]"
  };

  return (
    <motion.button
      className={`${baseClasses} ${variants[variant]} ${className}`}
      onClick={onClick}
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.95 }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <span className="relative z-10">{children}</span>
    </motion.button>
  );
};

// Feature Card Component
const FeatureCard = ({ icon, title, description, delay = 0 }: {
  icon: React.ReactNode;
  title: string;
  description: string;
  delay?: number;
}) => {
  return (
    <motion.div
      className="group relative p-8 bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl hover:border-blue-500/50 transition-all duration-300 hover:-translate-y-2 hover:shadow-[0_20px_40px_rgba(59,130,246,0.2)]"
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay }}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-blue-600/10 to-purple-600/10 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      
      <div className="relative z-10">
        <div className="text-4xl mb-4 text-blue-400 group-hover:text-blue-300 transition-colors duration-300">
          {icon}
        </div>
        <h3 className="text-xl font-bold text-white mb-3 group-hover:text-blue-100 transition-colors duration-300">
          {title}
        </h3>
        <p className="text-slate-300 group-hover:text-slate-200 transition-colors duration-300">
          {description}
        </p>
      </div>
    </motion.div>
  );
};

// Stats Counter Component
const StatsCounter = ({ end, label, delay = 0 }: { end: number; label: string; delay?: number }) => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      const increment = end / 50;
      const timer = setInterval(() => {
        setCount(prev => {
          if (prev >= end) {
            clearInterval(timer);
            return end;
          }
          return Math.min(prev + increment, end);
        });
      }, 30);
    }, delay * 1000);

    return () => clearTimeout(timer);
  }, [end, delay]);

  return (
    <motion.div
      className="text-center"
      initial={{ opacity: 0, scale: 0.5 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6, delay }}
    >
      <div className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
        {Math.floor(count).toLocaleString()}+
      </div>
      <div className="text-slate-300 mt-2">{label}</div>
    </motion.div>
  );
};

// Main Home Component
export default function Home() {
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    setIsLoaded(true);
  }, []);

  return (
    <div className="min-h-screen relative overflow-hidden">
      <AnimatedBackground />
      
      {/* Navigation */}
      <motion.nav 
        className="relative z-50 p-6"
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
      >
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <motion.div 
            className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400"
            whileHover={{ scale: 1.05 }}
          >
            HackerStats
          </motion.div>
          
          <div className="flex space-x-6">
            <motion.a 
              href="/graph" 
              className="text-slate-300 hover:text-blue-400 transition-colors duration-300 hover:-translate-y-0.5"
            >
              Graph
            </motion.a>
            <motion.a 
              href="/brainstorm" 
              className="text-slate-300 hover:text-blue-400 transition-colors duration-300 hover:-translate-y-0.5"
            >
              Brainstorm
            </motion.a>
            <motion.a 
              href="#contact" 
              className="text-slate-300 hover:text-blue-400 transition-colors duration-300 hover:-translate-y-0.5"
            >
              Contact
            </motion.a>
          </div>
        </div>
      </motion.nav>

      {/* Hero Section */}
      <section className="relative z-10 pt-20 pb-32">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.2 }}
          >
            <h1 className="text-6xl md:text-8xl font-bold mb-8">
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-400 to-blue-400">
                HackerStats
              </span>
            </h1>
            
            <motion.p 
              className="text-xl md:text-2xl text-slate-300 mb-12 max-w-4xl mx-auto leading-relaxed"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 1, delay: 0.6 }}
            >
              Discover the hidden connections in the hackathon universe. 
              Visualize projects, track hacker journeys, and unlock insights 
              from the world's largest hackathon database.
            </motion.p>

            <motion.div 
              className="flex flex-col sm:flex-row gap-6 justify-center items-center"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 1 }}
            >
              <GlowButton variant="primary" onClick={() => window.location.href = '/graph'}>
                Explore Graph
              </GlowButton>
              <GlowButton variant="secondary" onClick={() => window.location.href = '/brainstorm'}>
                Brainstorm
              </GlowButton>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="relative z-10 py-20">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div 
            className="text-center mb-16"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Powerful Features
            </h2>
            <p className="text-xl text-slate-300 max-w-3xl mx-auto">
              Two core experiences to explore hackathon projects and spark ideas.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-8">
            <FeatureCard
              icon="🌐"
              title="Graph Visualization"
              description="Interactive 3D graph visualization of hackathon projects, hackers, and their complex relationships."
              delay={0.1}
            />
            <FeatureCard
              icon="💡"
              title="Brainstorm"
              description="Describe a prompt and instantly see the top similar hackathon projects."
              delay={0.2}
            />
          </div>
        </div>
      </section>


      {/* CTA Section */}
      <section className="relative z-10 py-20">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-8">
              Ready to Explore?
            </h2>
            <p className="text-xl text-slate-300 mb-12">
              Join thousands of developers discovering new opportunities 
              and connections in the hackathon ecosystem.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-6 justify-center">
              <GlowButton variant="primary" onClick={() => window.location.href = '/graph'}>
                Explore Graph
              </GlowButton>
              <GlowButton variant="accent" onClick={() => window.location.href = '/brainstorm'}>
                Try Brainstorm
              </GlowButton>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer id="contact" className="relative z-10 py-12 border-t border-slate-700/50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-3 gap-8">
            <div>
              <h3 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400 mb-4">
                HackerStats
              </h3>
              <p className="text-slate-300">
                The ultimate platform for hackathon data analysis and visualization.
              </p>
            </div>
            
            <div>
              <h4 className="text-lg font-semibold text-white mb-4">Quick Links</h4>
              <div className="space-y-2">
                <a href="/graph" className="block text-slate-300 hover:text-blue-400 transition-colors duration-300 hover:-translate-y-0.5">
                  Graph Visualization
                </a>
                <a href="/brainstorm" className="block text-slate-300 hover:text-blue-400 transition-colors duration-300 hover:-translate-y-0.5">
                  Brainstorm
                </a>
                <a href="/api" className="block text-slate-300 hover:text-blue-400 transition-colors duration-300 hover:-translate-y-0.5">
                  API Documentation
                </a>
              </div>
            </div>
            
            <div>
              <h4 className="text-lg font-semibold text-white mb-4">Connect</h4>
              <div className="space-y-2">
                <p className="text-slate-300">GitHub: @hackerstats</p>
                <p className="text-slate-300">Email: contact@hackerstats.dev</p>
                <p className="text-slate-300">Discord: HackerStats Community</p>
              </div>
            </div>
          </div>
          
          <div className="mt-8 pt-8 border-t border-slate-700/50 text-center text-slate-400">
            <p>&copy; 2025 HackerStats. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
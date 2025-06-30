'use client'

import { useState } from 'react'
import { ChevronRightIcon, PlayIcon, CheckIcon } from '@heroicons/react/24/outline'
import { motion } from 'framer-motion'

const features = [
  {
    name: 'Data Analysis Agent',
    description: 'Automatically scans and analyzes your source platform structure',
    icon: '🔍',
  },
  {
    name: 'Migration Planning Agent',
    description: 'Creates detailed migration roadmaps with realistic timelines',
    icon: '📋',
  },
  {
    name: 'SEO Preservation Agent',
    description: 'Maintains search rankings with intelligent URL mapping',
    icon: '🎯',
  },
  {
    name: 'Customer Communication Agent',
    description: 'Drafts professional customer notifications and updates',
    icon: '📧',
  },
]

const platforms = [
  { name: 'Shopify', supported: true },
  { name: 'WooCommerce', supported: true },
  { name: 'Magento', supported: true },
  { name: 'BigCommerce', supported: true },
  { name: 'Ideasoft', supported: true },
  { name: 'Ikas', supported: true },
]

export default function HomePage() {
  const [selectedPlatform, setSelectedPlatform] = useState('shopify')

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="relative">
        <nav className="mx-auto max-w-7xl px-6 pt-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 flex items-center justify-center">
                <span className="text-white font-bold text-sm">MA</span>
              </div>
              <span className="text-xl font-bold text-gray-900">Migration Assistant</span>
            </div>
            <div className="hidden md:flex items-center space-x-8">
              <a href="#features" className="text-gray-600 hover:text-gray-900">Features</a>
              <a href="#platforms" className="text-gray-600 hover:text-gray-900">Platforms</a>
              <a href="#docs" className="text-gray-600 hover:text-gray-900">Documentation</a>
              <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                Get Started
              </button>
            </div>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="relative px-6 pt-14 lg:px-8">
        <div className="mx-auto max-w-4xl py-32 sm:py-48 lg:py-56">
          <div className="text-center">
            <motion.h1 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl"
            >
              Intelligent Store{' '}
              <span className="gradient-text">Migration Assistant</span>
            </motion.h1>
            
            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="mt-6 text-lg leading-8 text-gray-600 max-w-2xl mx-auto"
            >
              Enterprise-grade multi-agent system for seamless e-commerce platform migrations. 
              Migrate 2,000+ products with zero downtime while preserving SEO rankings and customer experience.
            </motion.p>
            
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.4 }}
              className="mt-10 flex items-center justify-center gap-x-6"
            >
              <button className="flex items-center gap-2 bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 rounded-lg transition-all">
                <PlayIcon className="h-4 w-4" />
                Start Migration
              </button>
              <a href="#demo" className="flex items-center gap-1 text-sm font-semibold leading-6 text-gray-900 hover:text-blue-600 transition-colors">
                Live Demo <ChevronRightIcon className="h-4 w-4" />
              </a>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 sm:py-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Multi-Agent Architecture
            </h2>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              Our intelligent agents work together to ensure a seamless migration experience
            </p>
          </div>
          
          <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
            <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-2">
              {features.map((feature, index) => (
                <motion.div
                  key={feature.name}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  viewport={{ once: true }}
                  className="flex flex-col"
                >
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-gray-900">
                    <span className="text-2xl">{feature.icon}</span>
                    {feature.name}
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-600">
                    <p className="flex-auto">{feature.description}</p>
                  </dd>
                </motion.div>
              ))}
            </dl>
          </div>
        </div>
      </section>

      {/* Platforms Section */}
      <section id="platforms" className="bg-white py-24 sm:py-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Supported Platforms
            </h2>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              Seamlessly migrate between major e-commerce platforms
            </p>
          </div>
          
          <div className="mx-auto mt-16 grid max-w-lg grid-cols-2 items-center gap-x-8 gap-y-12 sm:max-w-xl sm:grid-cols-3 sm:gap-x-10 lg:mx-0 lg:max-w-none lg:grid-cols-6">
            {platforms.map((platform) => (
              <div key={platform.name} className="text-center">
                <div className="flex items-center justify-center h-16 w-16 mx-auto bg-gray-100 rounded-lg mb-4">
                  <span className="text-sm font-medium text-gray-600">{platform.name.slice(0, 2)}</span>
                </div>
                <div className="flex items-center justify-center gap-2">
                  <span className="text-sm font-medium text-gray-900">{platform.name}</span>
                  {platform.supported && (
                    <CheckIcon className="h-4 w-4 text-green-500" />
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-blue-600">
        <div className="px-6 py-24 sm:px-6 sm:py-32 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Ready to migrate your store?
            </h2>
            <p className="mx-auto mt-6 max-w-xl text-lg leading-8 text-blue-100">
              Join thousands of merchants who have successfully migrated their stores with zero downtime.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <button className="bg-white px-6 py-3 text-sm font-semibold text-blue-600 shadow-sm hover:bg-blue-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white rounded-lg transition-all">
                Start Free Migration
              </button>
              <a href="#contact" className="text-sm font-semibold leading-6 text-white hover:text-blue-100 transition-colors">
                Contact Sales <span aria-hidden="true">→</span>
              </a>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
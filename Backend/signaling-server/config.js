/**
 * Shared configuration for GramOthi signaling server
 * Consolidates quality profiles and settings to avoid duplication
 */

// Video Quality Presets
const VIDEO_QUALITY_PRESETS = {
  ultra_low: {
    resolution: '320x240',
    bitrate: '50k',
    fps: 5,
    crf: 35,
    preset: 'ultrafast',
    description: 'Ultra Low - Emergency mode for very poor connections'
  },
  low: {
    resolution: '480x360',
    bitrate: '100k',
    fps: 10,
    crf: 32,
    preset: 'ultrafast',
    description: 'Low - Basic quality for poor connections'
  },
  medium: {
    resolution: '640x480',
    bitrate: '200k',
    fps: 15,
    crf: 28,
    preset: 'fast',
    description: 'Medium - Balanced quality and bandwidth'
  },
  high: {
    resolution: '854x480',
    bitrate: '400k',
    fps: 24,
    crf: 25,
    preset: 'medium',
    description: 'High - Good quality for stable connections'
  },
  very_high: {
    resolution: '1280x720',
    bitrate: '800k',
    fps: 30,
    crf: 22,
    preset: 'slow',
    description: 'Very High - Excellent quality for good connections'
  },
  ultra_high: {
    resolution: '1920x1080',
    bitrate: '1500k',
    fps: 30,
    crf: 20,
    preset: 'slower',
    description: 'Ultra High - Best quality for excellent connections'
  }
};

// Adaptive streaming profiles for poor networks
const ADAPTIVE_PROFILES = {
  emergency: {
    audio: { bitrate: '8k', sampleRate: 16000, channels: 1, codec: 'opus' },
    video: { bitrate: '25k', fps: 3, resolution: '240x180', codec: 'h264' },
    network: { bufferSize: 512, chunkSize: 256, retryAttempts: 5, timeout: 30000 }
  },
  critical: {
    audio: { bitrate: '16k', sampleRate: 22050, channels: 1, codec: 'opus' },
    video: { bitrate: '50k', fps: 5, resolution: '320x240', codec: 'h264' },
    network: { bufferSize: 1024, chunkSize: 512, retryAttempts: 3, timeout: 20000 }
  },
  poor: {
    audio: { bitrate: '32k', sampleRate: 44100, channels: 1, codec: 'opus' },
    video: { bitrate: '100k', fps: 10, resolution: '480x360', codec: 'h264' },
    network: { bufferSize: 2048, chunkSize: 1024, retryAttempts: 2, timeout: 15000 }
  },
  fair: {
    audio: { bitrate: '64k', sampleRate: 44100, channels: 2, codec: 'opus' },
    video: { bitrate: '200k', fps: 15, resolution: '640x480', codec: 'h264' },
    network: { bufferSize: 4096, chunkSize: 2048, retryAttempts: 2, timeout: 10000 }
  },
  good: {
    audio: { bitrate: '128k', sampleRate: 44100, channels: 2, codec: 'opus' },
    video: { bitrate: '400k', fps: 24, resolution: '854x480', codec: 'h264' },
    network: { bufferSize: 8192, chunkSize: 4096, retryAttempts: 1, timeout: 8000 }
  },
  excellent: {
    audio: { bitrate: '192k', sampleRate: 48000, channels: 2, codec: 'opus' },
    video: { bitrate: '800k', fps: 30, resolution: '1280x720', codec: 'h264' },
    network: { bufferSize: 16384, chunkSize: 8192, retryAttempts: 1, timeout: 5000 }
  }
};

/**
 * Get video quality configuration
 */
function getVideoQualityConfig(qualityPreset, customSettings) {
  if (customSettings) {
    return {
      preset: 'custom',
      settings: customSettings,
      isCustom: true
    };
  }
  
  const preset = VIDEO_QUALITY_PRESETS[qualityPreset] || VIDEO_QUALITY_PRESETS.medium;
  
  return {
    preset: qualityPreset,
    settings: preset,
    isCustom: false
  };
}

/**
 * Get adaptive configuration based on network quality
 */
function getAdaptiveConfig(bandwidth, qualityMetrics, contentType) {
  let profile = 'fair'; // Default profile
  
  // Determine profile based on bandwidth and quality metrics
  if (qualityMetrics) {
    const { latency, packetLoss, jitter } = qualityMetrics;
    
    if (latency > 1000 || packetLoss > 10) {
      profile = 'emergency';
    } else if (latency > 500 || packetLoss > 5) {
      profile = 'critical';
    } else if (latency > 200 || packetLoss > 2) {
      profile = 'poor';
    } else if (latency < 50 && packetLoss < 0.5 && jitter < 10) {
      profile = 'excellent';
    } else if (latency < 100 && packetLoss < 1) {
      profile = 'good';
    }
  } else if (bandwidth) {
    // Fallback to bandwidth-based selection
    switch (bandwidth) {
      case 'ultra_low': profile = 'emergency'; break;
      case 'very_low': profile = 'critical'; break;
      case 'low': profile = 'poor'; break;
      case 'medium': profile = 'fair'; break;
      case 'high': profile = 'good'; break;
      case 'ultra_high': profile = 'excellent'; break;
    }
  }
  
  const config = ADAPTIVE_PROFILES[profile];
  
  return {
    profile: profile,
    contentType: contentType,
    audio: config.audio,
    video: config.video,
    network: config.network,
    optimization: {
      adaptiveBitrate: true,
      errorRecovery: true,
      bufferingStrategy: profile.includes('emergency') || profile.includes('critical') ? 'aggressive' : 'balanced',
      fallbackEnabled: true
    }
  };
}

/**
 * Get video quality recommendations based on network conditions
 */
function getVideoQualityRecommendations(networkConditions) {
  const { latency, bandwidth, packetLoss } = networkConditions;
  
  const recommendations = [];
  
  // Analyze each preset for suitability
  for (const [presetName, presetSettings] of Object.entries(VIDEO_QUALITY_PRESETS)) {
    const suitabilityScore = calculatePresetSuitability(presetSettings, latency, bandwidth, packetLoss);
    
    recommendations.push({
      preset: presetName,
      settings: presetSettings,
      suitabilityScore: suitabilityScore,
      recommended: suitabilityScore >= 80
    });
  }
  
  // Sort by suitability score
  recommendations.sort((a, b) => b.suitabilityScore - a.suitabilityScore);
  
  return {
    recommendations: recommendations,
    topRecommendation: recommendations[0],
    networkConditions: networkConditions
  };
}

/**
 * Calculate how suitable a preset is for given network conditions
 */
function calculatePresetSuitability(presetSettings, latency, bandwidth, packetLoss) {
  try {
    // Extract preset parameters
    const bitrateStr = presetSettings.bitrate;
    const bitrateValue = parseInt(bitrateStr.replace('k', '').replace('M', '000'));
    const fps = presetSettings.fps;
    const resolution = presetSettings.resolution;
    
    // Calculate resolution complexity
    const [width, height] = resolution.split('x').map(Number);
    const pixelCount = width * height;
    
    // Calculate suitability score (0-100)
    let score = 100;
    
    // Penalty for high bitrate on low bandwidth
    if (bandwidth < bitrateValue * 1.5) {
      score -= 30;
    }
    
    // Penalty for high FPS on high latency
    if (latency > 200 && fps > 20) {
      score -= 20;
    }
    
    // Penalty for high resolution on poor network
    if (packetLoss > 2 && pixelCount > 640 * 480) {
      score -= 25;
    }
    
    // Bonus for appropriate settings
    if (latency < 100 && fps >= 24) {
      score += 10;
    }
    
    if (packetLoss < 1 && pixelCount >= 1280 * 720) {
      score += 15;
    }
    
    return Math.max(0, Math.min(100, score));
    
  } catch (error) {
    console.error('Error calculating preset suitability:', error);
    return 50; // Default moderate suitability
  }
}

module.exports = {
  VIDEO_QUALITY_PRESETS,
  ADAPTIVE_PROFILES,
  getVideoQualityConfig,
  getAdaptiveConfig,
  getVideoQualityRecommendations,
  calculatePresetSuitability
};

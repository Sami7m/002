import React, { useState, useEffect } from 'react';
import { Car, Gauge, Thermometer, Droplet, Wind, AlertTriangle, Wifi, WifiOff, Download, RotateCw } from 'lucide-react';

function App() {
  const [connected, setConnected] = useState(false);
  const [selectedVehicle, setSelectedVehicle] = useState('auto');
  const [metrics, setMetrics] = useState({
    speed: 0,
    rpm: 0,
    engineTemp: 0,
    fuelLevel: 75,
    intakePressure: 0,
    // Vehicle specific metrics
    turboPressure: 0,
    clutchStatus: 0,
    fuelConsumption: 0,
    hybridBattery: 0,
    boostPressure: 0,
    oilTemp: 0
  });
  const [dtcCodes, setDtcCodes] = useState([]);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [graphMetric, setGraphMetric] = useState('speed');
  const [graphData, setGraphData] = useState(Array(30).fill(0));
  const [connectionStatus, setConnectionStatus] = useState('');

  // Colors from the Python app
  const COLORS = {
    background: "#2C2F33",
    text: "#FFFFFF",
    accent: "#7289DA",
    accentHover: "#5B6EBF",
    success: "#43B581",
    error: "#FF5555",
    warning: "#FAA61A",
    graphLine: "#7289DA",
    graphBackground: "#2C2F33",
    gridLine: "#3E4147"
  };

  // Mock DTC codes
  const DTC_CODES = {
    "P0100": "Mass or Volume Air Flow Circuit Malfunction",
    "P0171": "System Too Lean (Bank 1)",
    "P0300": "Random/Multiple Cylinder Misfire Detected",
    "P0420": "Catalyst System Efficiency Below Threshold (Bank 1)"
  };

  // Connect to OBD (simulated)
  const connectOBD = () => {
    setConnectionStatus('Connecting...');
    
    // Simulate connection delay
    setTimeout(() => {
      setConnected(true);
      setConnectionStatus('Connected to ELM327 (192.168.0.10:35000)');
      
      // Start updating metrics
      startMetricUpdates();
    }, 1500);
  };

  // Disconnect from OBD (simulated)
  const disconnectOBD = () => {
    setConnected(false);
    setConnectionStatus('Disconnected');
  };

  // Read DTCs (simulated)
  const readDTC = () => {
    setConnectionStatus('Reading DTCs...');
    
    // Simulate reading delay
    setTimeout(() => {
      const codes = Object.entries(DTC_CODES)
        .filter(() => Math.random() > 0.5) // Randomly include some codes
        .map(([code, description]) => ({ code, description }));
      
      setDtcCodes(codes);
      setConnectionStatus(codes.length > 0 
        ? `Found ${codes.length} diagnostic trouble codes` 
        : 'No DTCs found');
      
      // Switch to diagnostics tab if codes found
      if (codes.length > 0) {
        setActiveTab('diagnostics');
      }
    }, 1000);
  };

  // Clear DTCs (simulated)
  const clearDTC = () => {
    setConnectionStatus('Clearing DTCs...');
    
    // Simulate clearing delay
    setTimeout(() => {
      setDtcCodes([]);
      setConnectionStatus('DTCs cleared successfully');
    }, 1000);
  };

  // Export data (simulated)
  const exportData = () => {
    setConnectionStatus('Exporting data...');
    
    // Simulate export delay
    setTimeout(() => {
      setConnectionStatus('Data exported to obd_data.csv');
      
      // Create a fake CSV download
      const element = document.createElement('a');
      const file = new Blob(['timestamp,speed,rpm,engine_temp,fuel_level\n' + 
                            '2025-06-28 14:30:00,65,2100,87,75'], 
                            {type: 'text/csv'});
      element.href = URL.createObjectURL(file);
      element.download = 'obd_data.csv';
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
    }, 1000);
  };

  // Simulate metric updates
  const startMetricUpdates = () => {
    const interval = setInterval(() => {
      if (!connected) {
        clearInterval(interval);
        return;
      }
      
      // Generate random fluctuations for metrics
      const newMetrics = {
        speed: Math.max(0, metrics.speed + (Math.random() * 10 - 5)),
        rpm: Math.max(800, metrics.rpm + (Math.random() * 200 - 100)),
        engineTemp: Math.min(95, Math.max(80, metrics.engineTemp + (Math.random() * 2 - 1))),
        fuelLevel: Math.max(0, Math.min(100, metrics.fuelLevel + (Math.random() * 0.2 - 0.1))),
        intakePressure: Math.max(0, metrics.intakePressure + (Math.random() * 5 - 2.5)),
        // Vehicle specific metrics
        turboPressure: Math.max(0, metrics.turboPressure + (Math.random() * 10 - 5)),
        clutchStatus: Math.random() > 0.95 ? (metrics.clutchStatus === 0 ? 1 : 0) : metrics.clutchStatus,
        fuelConsumption: Math.max(0, metrics.fuelConsumption + (Math.random() * 0.5 - 0.25)),
        hybridBattery: Math.max(0, Math.min(100, metrics.hybridBattery + (Math.random() * 2 - 1))),
        boostPressure: Math.max(0, metrics.boostPressure + (Math.random() * 10 - 5)),
        oilTemp: Math.min(110, Math.max(70, metrics.oilTemp + (Math.random() * 2 - 1)))
      };
      
      setMetrics(newMetrics);
      
      // Update graph data
      setGraphData(prevData => {
        const newData = [...prevData];
        newData.shift();
        newData.push(newMetrics[graphMetric]);
        return newData;
      });
    }, 1000);
    
    return () => clearInterval(interval);
  };

  // Initialize some metrics on first load
  useEffect(() => {
    setMetrics({
      ...metrics,
      rpm: 850,
      engineTemp: 82,
      oilTemp: 85
    });
  }, []);

  // Vehicle-specific metrics based on selection
  const getVehicleSpecificMetrics = () => {
    switch (selectedVehicle) {
      case 'fiat':
        return (
          <>
            <div className="metric-item">
              <div className="metric-label">Turbo Pressure:</div>
              <div className="metric-value">{metrics.turboPressure.toFixed(1)} kPa</div>
            </div>
            <div className="metric-item">
              <div className="metric-label">Clutch Status:</div>
              <div className="metric-value">{metrics.clutchStatus === 0 ? 'Disengaged' : 'Engaged'}</div>
            </div>
          </>
        );
      case 'toyota':
        return (
          <>
            <div className="metric-item">
              <div className="metric-label">Fuel Consumption:</div>
              <div className="metric-value">{metrics.fuelConsumption.toFixed(1)} L/100km</div>
            </div>
            <div className="metric-item">
              <div className="metric-label">Hybrid Battery:</div>
              <div className="metric-value">{metrics.hybridBattery.toFixed(1)} %</div>
            </div>
          </>
        );
      case 'vag':
        return (
          <>
            <div className="metric-item">
              <div className="metric-label">Boost Pressure:</div>
              <div className="metric-value">{metrics.boostPressure.toFixed(1)} kPa</div>
            </div>
            <div className="metric-item">
              <div className="metric-label">Oil Temperature:</div>
              <div className="metric-value">{metrics.oilTemp.toFixed(1)} °C</div>
            </div>
          </>
        );
      default:
        return null;
    }
  };

  // Render the graph
  const renderGraph = () => {
    const maxValue = Math.max(...graphData, 1);
    const normalizedData = graphData.map(value => (value / maxValue) * 100);
    
    return (
      <div className="graph-container">
        <div className="graph-title">
          {graphMetric === 'speed' ? 'Speed (km/h)' : 
           graphMetric === 'rpm' ? 'RPM' : 
           graphMetric === 'engineTemp' ? 'Engine Temperature (°C)' : 
           graphMetric === 'fuelLevel' ? 'Fuel Level (%)' : 
           graphMetric === 'intakePressure' ? 'Intake Pressure (kPa)' : 
           graphMetric === 'turboPressure' ? 'Turbo Pressure (kPa)' : 
           graphMetric === 'fuelConsumption' ? 'Fuel Consumption (L/100km)' : 
           graphMetric === 'hybridBattery' ? 'Hybrid Battery (%)' : 
           graphMetric === 'boostPressure' ? 'Boost Pressure (kPa)' : 
           graphMetric === 'oilTemp' ? 'Oil Temperature (°C)' : 
           'Value'}
        </div>
        <div className="graph">
          <div className="graph-y-axis">
            <div className="graph-y-label">{maxValue.toFixed(0)}</div>
            <div className="graph-y-label">{(maxValue/2).toFixed(0)}</div>
            <div className="graph-y-label">0</div>
          </div>
          <div className="graph-plot">
            {normalizedData.map((value, index) => (
              <div 
                key={index} 
                className="graph-bar" 
                style={{ height: `${value}%` }}
              />
            ))}
          </div>
        </div>
        <div className="graph-x-axis">
          <div className="graph-x-label">-30s</div>
          <div className="graph-x-label">-15s</div>
          <div className="graph-x-label">Now</div>
        </div>
      </div>
    );
  };

  return (
    <div className="app-container" style={{ backgroundColor: COLORS.background, color: COLORS.text }}>
      <header className="app-header">
        <div className="app-title">
          <Car size={24} />
          <h1>OBD-II Diagnostic Tool</h1>
        </div>
        
        <div className="connection-controls">
          <div className="vehicle-selector">
            <label htmlFor="vehicle">Vehicle:</label>
            <select 
              id="vehicle" 
              value={selectedVehicle} 
              onChange={(e) => setSelectedVehicle(e.target.value)}
              disabled={connected}
            >
              <option value="auto">Auto Detect</option>
              <option value="fiat">Fiat 500 Series 1</option>
              <option value="toyota">Toyota C-HR/Corolla</option>
              <option value="vag">Volkswagen Group</option>
            </select>
          </div>
          
          <div className="connection-status" style={{ color: connected ? COLORS.success : COLORS.error }}>
            {connected ? <Wifi size={20} /> : <WifiOff size={20} />}
          </div>
          
          <div className="connection-buttons">
            <button 
              className="btn btn-primary" 
              onClick={connectOBD} 
              disabled={connected}
              style={{ 
                backgroundColor: connected ? '#3E4147' : COLORS.accent,
                color: connected ? '#8E9297' : COLORS.text
              }}
            >
              Connect
            </button>
            
            <button 
              className="btn btn-secondary" 
              onClick={disconnectOBD} 
              disabled={!connected}
              style={{ 
                backgroundColor: !connected ? '#3E4147' : COLORS.accent,
                color: !connected ? '#8E9297' : COLORS.text
              }}
            >
              Disconnect
            </button>
            
            <button 
              className="btn btn-secondary" 
              onClick={readDTC} 
              disabled={!connected}
              style={{ 
                backgroundColor: !connected ? '#3E4147' : COLORS.accent,
                color: !connected ? '#8E9297' : COLORS.text
              }}
            >
              <AlertTriangle size={16} />
              Read DTCs
            </button>
            
            <button 
              className="btn btn-secondary" 
              onClick={clearDTC} 
              disabled={!connected || dtcCodes.length === 0}
              style={{ 
                backgroundColor: (!connected || dtcCodes.length === 0) ? '#3E4147' : COLORS.accent,
                color: (!connected || dtcCodes.length === 0) ? '#8E9297' : COLORS.text
              }}
            >
              <RotateCw size={16} />
              Clear DTCs
            </button>
            
            <button 
              className="btn btn-secondary" 
              onClick={exportData} 
              disabled={!connected}
              style={{ 
                backgroundColor: !connected ? '#3E4147' : COLORS.accent,
                color: !connected ? '#8E9297' : COLORS.text
              }}
            >
              <Download size={16} />
              Export
            </button>
          </div>
        </div>
      </header>
      
      <div className="tab-controls">
        <button 
          className={`tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
          style={{ 
            backgroundColor: activeTab === 'dashboard' ? COLORS.accent : '#3E4147',
            color: COLORS.text
          }}
        >
          Dashboard
        </button>
        <button 
          className={`tab-btn ${activeTab === 'diagnostics' ? 'active' : ''}`}
          onClick={() => setActiveTab('diagnostics')}
          style={{ 
            backgroundColor: activeTab === 'diagnostics' ? COLORS.accent : '#3E4147',
            color: COLORS.text
          }}
        >
          Diagnostics
        </button>
      </div>
      
      <main className="app-content">
        {activeTab === 'dashboard' ? (
          <div className="dashboard">
            <div className="metrics-grid">
              <div className="metric-item">
                <div className="metric-icon"><Gauge size={24} /></div>
                <div className="metric-label">Speed:</div>
                <div className="metric-value">{metrics.speed.toFixed(1)} km/h</div>
              </div>
              
              <div className="metric-item">
                <div className="metric-icon"><Gauge size={24} /></div>
                <div className="metric-label">RPM:</div>
                <div className="metric-value">{metrics.rpm.toFixed(0)}</div>
              </div>
              
              <div className="metric-item">
                <div className="metric-icon"><Thermometer size={24} /></div>
                <div className="metric-label">Engine Temp:</div>
                <div className="metric-value">{metrics.engineTemp.toFixed(1)} °C</div>
              </div>
              
              <div className="metric-item">
                <div className="metric-icon"><Droplet size={24} /></div>
                <div className="metric-label">Fuel Level:</div>
                <div className="metric-value">{metrics.fuelLevel.toFixed(1)} %</div>
              </div>
              
              <div className="metric-item">
                <div className="metric-icon"><Wind size={24} /></div>
                <div className="metric-label">Intake Pressure:</div>
                <div className="metric-value">{metrics.intakePressure.toFixed(1)} kPa</div>
              </div>
              
              {/* Vehicle-specific metrics */}
              {getVehicleSpecificMetrics()}
            </div>
            
            <div className="graph-controls">
              <label htmlFor="graph-metric">Graph:</label>
              <select 
                id="graph-metric" 
                value={graphMetric} 
                onChange={(e) => setGraphMetric(e.target.value)}
              >
                <option value="speed">Speed</option>
                <option value="rpm">RPM</option>
                <option value="engineTemp">Engine Temperature</option>
                <option value="fuelLevel">Fuel Level</option>
                <option value="intakePressure">Intake Pressure</option>
                {selectedVehicle === 'fiat' && (
                  <>
                    <option value="turboPressure">Turbo Pressure</option>
                    <option value="clutchStatus">Clutch Status</option>
                  </>
                )}
                {selectedVehicle === 'toyota' && (
                  <>
                    <option value="fuelConsumption">Fuel Consumption</option>
                    <option value="hybridBattery">Hybrid Battery</option>
                  </>
                )}
                {selectedVehicle === 'vag' && (
                  <>
                    <option value="boostPressure">Boost Pressure</option>
                    <option value="oilTemp">Oil Temperature</option>
                  </>
                )}
              </select>
            </div>
            
            {renderGraph()}
          </div>
        ) : (
          <div className="diagnostics">
            <h2>Diagnostic Trouble Codes</h2>
            
            {dtcCodes.length > 0 ? (
              <table className="dtc-table">
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Description</th>
                  </tr>
                </thead>
                <tbody>
                  {dtcCodes.map((dtc, index) => (
                    <tr key={index} className={index % 2 === 0 ? 'even' : 'odd'}>
                      <td>{dtc.code}</td>
                      <td>{dtc.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="no-dtc">No DTCs found</div>
            )}
          </div>
        )}
      </main>
      
      <footer className="app-footer">
        <div className="status-bar">{connectionStatus}</div>
      </footer>
    </div>
  );
}

export default App;
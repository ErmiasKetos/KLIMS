"use client"

import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface EquipmentData {
  id: string
  name: string
  status: string
  lastReading: string
}

export function EquipmentIntegration() {
  const [equipmentData, setEquipmentData] = useState<EquipmentData[]>([])

  useEffect(() => {
    // Simulating data fetch from equipment
    const fetchData = () => {
      const mockData: EquipmentData[] = [
        { id: '1', name: 'Spectrophotometer', status: 'Online', lastReading: '0.75 Abs' },
        { id: '2', name: 'pH Meter', status: 'Online', lastReading: 'pH 7.2' },
        { id: '3', name: 'Centrifuge', status: 'Offline', lastReading: 'N/A' },
      ]
      setEquipmentData(mockData)
    }

    fetchData()
    const interval = setInterval(fetchData, 5000) // Refresh every 5 seconds

    return () => clearInterval(interval)
  }, [])

  const handleCalibrate = (id: string) => {
    // Implement calibration logic here
    console.log(`Calibrating equipment ${id}`)
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Equipment Integration</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {equipmentData.map((equipment) => (
          <Card key={equipment.id}>
            <CardHeader>
              <CardTitle>{equipment.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Status: {equipment.status}</p>
              <p>Last Reading: {equipment.lastReading}</p>
              <Button
                onClick={() => handleCalibrate(equipment.id)}
                className="mt-2"
              >
                Calibrate
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}


"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { LineChart, BarChart, PieChart } from "@/components/ui/chart"

export function Analytics() {
  const [data, setData] = useState({
    jobTrends: [],
    experimentPopularity: [],
    inventoryLevels: [],
  })

  useEffect(() => {
    // Fetch data from API
    const fetchData = async () => {
      // In a real application, these would be API calls
      const jobTrends = [
        { date: '2023-01', completed: 10, inProgress: 5 },
        { date: '2023-02', completed: 15, inProgress: 8 },
        { date: '2023-03', completed: 20, inProgress: 10 },
        { date: '2023-04', completed: 18, inProgress: 12 },
      ]

      const experimentPopularity = [
        { name: 'Exp 1', count: 25 },
        { name: 'Exp 2', count: 18 },
        { name: 'Exp 3', count: 15 },
        { name: 'Exp 4', count: 12 },
        { name: 'Exp 5', count: 10 },
      ]

      const inventoryLevels = [
        { reagent: 'KR1E', quantity: 500 },
        { reagent: 'KR1S', quantity: 350 },
        { reagent: 'KR2S', quantity: 400 },
        { reagent: 'KR3E', quantity: 600 },
        { reagent: 'KR3S', quantity: 450 },
      ]

      setData({ jobTrends, experimentPopularity, inventoryLevels })
    }

    fetchData()
  }, [])

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Analytics</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Job Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <LineChart
              data={data.jobTrends}
              index="date"
              categories={["completed", "inProgress"]}
              colors={["emerald", "blue"]}
              valueFormatter={(value) => `${value} jobs`}
              className="h-72"
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Experiment Popularity</CardTitle>
          </CardHeader>
          <CardContent>
            <PieChart
              data={data.experimentPopularity}
              index="name"
              category="count"
              className="h-72"
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Inventory Levels</CardTitle>
          </CardHeader>
          <CardContent>
            <BarChart
              data={data.inventoryLevels}
              index="reagent"
              categories={["quantity"]}
              colors={["violet"]}
              valueFormatter={(value) => `${value} units`}
              className="h-72"
            />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}


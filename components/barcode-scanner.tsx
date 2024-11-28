"use client"

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

interface ScannedItem {
  id: string
  name: string
  quantity: number
}

export function BarcodeScanner() {
  const [scannedItems, setScannedItems] = useState<ScannedItem[]>([])
  const [barcodeInput, setBarcodeInput] = useState('')

  const handleScan = () => {
    // In a real application, this would interface with a barcode scanner
    // For this example, we'll simulate scanning by using the input value
    const newItem: ScannedItem = {
      id: barcodeInput,
      name: `Item ${barcodeInput}`,
      quantity: 1,
    }
    setScannedItems([...scannedItems, newItem])
    setBarcodeInput('')
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Barcode Scanner</h2>
      <div className="flex gap-4 mb-4">
        <Input
          type="text"
          placeholder="Enter barcode"
          value={barcodeInput}
          onChange={(e) => setBarcodeInput(e.target.value)}
        />
        <Button onClick={handleScan}>Scan</Button>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Barcode</TableHead>
            <TableHead>Item Name</TableHead>
            <TableHead>Quantity</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {scannedItems.map((item) => (
            <TableRow key={item.id}>
              <TableCell>{item.id}</TableCell>
              <TableCell>{item.name}</TableCell>
              <TableCell>{item.quantity}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}


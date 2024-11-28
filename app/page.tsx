"use client"

import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { RequestManagement } from "./components/request-management"
import { TrayConfiguration } from "./components/tray-configuration"
import { InventoryManagement } from "./components/inventory-management"
import { ProductionAndQC } from "./components/production-and-qc"
import { ShippingAndLogging } from "./components/shipping-and-logging"
import { Analytics } from "./components/analytics"
import { EquipmentIntegration } from "./components/equipment-integration"
import { BarcodeScanner } from "./components/barcode-scanner"

export default function ReagentTrayLIMS() {
  const [activeTab, setActiveTab] = useState("requests")

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4">Reagent Tray LIMS</h1>
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-8 gap-4">
          <TabsTrigger value="requests">Requests</TabsTrigger>
          <TabsTrigger value="configuration">Tray Configuration</TabsTrigger>
          <TabsTrigger value="inventory">Inventory</TabsTrigger>
          <TabsTrigger value="production">Production & QC</TabsTrigger>
          <TabsTrigger value="shipping">Shipping & Logging</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="equipment">Equipment</TabsTrigger>
          <TabsTrigger value="barcode">Barcode Scanner</TabsTrigger>
        </TabsList>
        <TabsContent value="requests">
          <RequestManagement />
        </TabsContent>
        <TabsContent value="configuration">
          <TrayConfiguration />
        </TabsContent>
        <TabsContent value="inventory">
          <InventoryManagement />
        </TabsContent>
        <TabsContent value="production">
          <ProductionAndQC />
        </TabsContent>
        <TabsContent value="shipping">
          <ShippingAndLogging />
        </TabsContent>
        <TabsContent value="analytics">
          <Analytics />
        </TabsContent>
        <TabsContent value="equipment">
          <EquipmentIntegration />
        </TabsContent>
        <TabsContent value="barcode">
          <BarcodeScanner />
        </TabsContent>
      </Tabs>
    </div>
  )
}


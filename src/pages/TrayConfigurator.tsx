import React, { useState, useEffect } from 'react';
import { Box, Button, VStack, HStack, Text, Select, useToast } from "@chakra-ui/react"
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import axios from 'axios';
import TrayVisualization from '../components/TrayVisualization';
import ResultsSummary from '../components/ResultsSummary';

const TrayConfigurator = () => {
  const [experiments, setExperiments] = useState([]);
  const [selectedExperiments, setSelectedExperiments] = useState([]);
  const [configuration, setConfiguration] = useState(null);
  const toast = useToast();

  useEffect(() => {
    fetchExperiments();
  }, []);

  const fetchExperiments = async () => {
    try {
      const response = await axios.get('/api/experiments');
      setExperiments(response.data);
    } catch (error) {
      toast({
        title: "Error fetching experiments",
        description: error.message,
        status: "error",
        duration: 9000,
        isClosable: true,
      });
    }
  };

  const handleExperimentSelect = (event) => {
    const value = parseInt(event.target.value);
    if (!selectedExperiments.includes(value)) {
      setSelectedExperiments([...selectedExperiments, value]);
    }
  };

  const handleExperimentRemove = (exp) => {
    setSelectedExperiments(selectedExperiments.filter(e => e !== exp));
  };

  const handleOptimize = async () => {
    try {
      const response = await axios.post('/api/optimize', { experiments: selectedExperiments });
      setConfiguration(response.data);
    } catch (error) {
      toast({
        title: "Optimization failed",
        description: error.response.data.message,
        status: "error",
        duration: 9000,
        isClosable: true,
      });
    }
  };

  const onDragEnd = (result) => {
    if (!result.destination) return;

    const newConfig = Array.from(configuration.tray_locations);
    const [reorderedItem] = newConfig.splice(result.source.index, 1);
    newConfig.splice(result.destination.index, 0, reorderedItem);

    setConfiguration({
      ...configuration,
      tray_locations: newConfig
    });
  };

  return (
    <Box>
      <VStack spacing={4} align="stretch">
        <HStack>
          <Select placeholder="Select experiment" onChange={handleExperimentSelect}>
            {experiments.map(exp => (
              <option key={exp.id} value={exp.id}>{exp.name}</option>
            ))}
          </Select>
          <Button colorScheme="blue" onClick={handleOptimize}>Optimize</Button>
        </HStack>
        <HStack>
          {selectedExperiments.map(exp => (
            <Button key={exp} onClick={() => handleExperimentRemove(exp)}>
              {experiments.find(e => e.id === exp)?.name} ✕
            </Button>
          ))}
        </HStack>
        {configuration && (
          <DragDropContext onDragEnd={onDragEnd}>
            <Droppable droppableId="tray">
              {(provided) => (
                <div {...provided.droppableProps} ref={provided.innerRef}>
                  <TrayVisualization configuration={configuration} />
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </DragDropContext>
        )}
        {configuration && <ResultsSummary configuration={configuration} />}
      </VStack>
    </Box>
  );
};

export default TrayConfigurator;


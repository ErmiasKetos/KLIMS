import React from 'react';
import { Box, SimpleGrid, Text } from "@chakra-ui/react"
import { Draggable } from 'react-beautiful-dnd';

const getReagentColor = (reagentCode) => {
  const colorMap = {
    'gray': ['KR1E', 'KR1S', 'KR2S', 'KR3E', 'KR3S'],
    'purple': ['KR7E1', 'KR7E2', 'KR8E1', 'KR8E2'],
    'green': ['KR9E1', 'KR9E2', 'KR17E1', 'KR17E2'],
    'orange': ['KR10E1', 'KR10E2', 'KR10E3'],
    'blue': ['KR16E1', 'KR16E2', 'KR16E3', 'KR16E4'],
    'red': ['KR29E1', 'KR29E2', 'KR29E3'],
    'yellow': ['KR35E1', 'KR35E2']
  };

  for (const [color, reagents] of Object.entries(colorMap)) {
    if (reagents.some(r => reagentCode.startsWith(r))) {
      return color;
    }
  }
  return 'gray.200';
};

const TrayVisualization = ({ configuration }) => {
  return (
    <SimpleGrid columns={4} spacing={2}>
      {configuration.tray_locations.map((location, index) => (
        <Draggable key={index} draggableId={`location-${index}`} index={index}>
          {(provided) => (
            <Box
              ref={provided.innerRef}
              {...provided.draggableProps}
              {...provided.dragHandleProps}
              bg={location ? getReagentColor(location.reagent_code) : 'gray.200'}
              p={2}
              borderRadius="md"
              boxShadow="md"
            >
              <Text fontWeight="bold">LOC-{index + 1}</Text>
              {location && (
                <>
                  <Text>{location.reagent_code}</Text>
                  <Text>Tests: {location.tests_possible}</Text>
                  <Text>Exp: #{location.experiment}</Text>
                </>
              )}
            </Box>
          )}
        </Draggable>
      ))}
    </SimpleGrid>
  );
};

export default TrayVisualization;


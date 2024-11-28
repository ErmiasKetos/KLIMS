import React from 'react';
import { Box, VStack, Text, Heading, Accordion, AccordionItem, AccordionButton, AccordionPanel, AccordionIcon } from "@chakra-ui/react"

const ResultsSummary = ({ configuration }) => {
  const trayLife = Math.min(...Object.values(configuration.results).map(r => r.total_tests));

  return (
    <Box>
      <Heading size="md" mb={4}>Results Summary</Heading>
      <Text fontWeight="bold" mb={2}>Tray Life: {trayLife} tests</Text>
      <Accordion allowMultiple>
        {Object.entries(configuration.results).map(([expNum, result]) => (
          <AccordionItem key={expNum}>
            <h2>
              <AccordionButton>
                <Box flex="1" textAlign="left">
                  {result.name} (#{expNum}) - {result.total_tests} total tests
                </Box>
                <AccordionIcon />
              </AccordionButton>
            </h2>
            <AccordionPanel pb={4}>
              {result.sets.map((set, index) => (
                <VStack key={index} align="stretch" mt={2}>
                  <Text fontWeight="bold">{index === 0 ? "Primary Set:" : `Additional Set ${index + 1}:`}</Text>
                  {set.placements.map((placement, i) => (
                    <Text key={i}>
                      {placement.reagent_code} (LOC-{placement.location + 1}): {placement.tests} tests possible
                    </Text>
                  ))}
                  <Text>Tests from this set: {set.tests_per_set}</Text>
                </VStack>
              ))}
            </AccordionPanel>
          </AccordionItem>
        ))}
      </Accordion>
    </Box>
  );
};

export default ResultsSummary;


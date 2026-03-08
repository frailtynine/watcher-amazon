import { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Heading,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Button,
  HStack,
  Text,
  Select,
  Alert,
  AlertIcon,
  Spinner,
  Center,
  useDisclosure,
  VStack,
  Badge,
  Tooltip,
  Icon,
} from '@chakra-ui/react';
import { CheckCircleIcon, WarningIcon, InfoIcon } from '@chakra-ui/icons';
import { useGetNewsItemsQuery, useGetSourcesQuery } from '../../services/api';
import { NewsItem } from '../../types';
import NewsItemDetail from './NewsItemDetail';

export default function NewsItemsPage() {
  const [selectedItem, setSelectedItem] = useState<NewsItem | null>(null);
  const [skip, setSkip] = useState(0);
  const [limit] = useState(20);
  const [sourceId, setSourceId] = useState<number | undefined>(undefined);
  const [newsItemsWithResults, setNewsItemsWithResults] = useState<NewsItem[]>([]);

  const { isOpen, onOpen, onClose } = useDisclosure();

  const { data: newsItems, isLoading, error } = useGetNewsItemsQuery({
    skip,
    limit,
    source_id: sourceId,
  });

  const { data: sources } = useGetSourcesQuery();

  // Fetch processing results for all displayed news items
  useEffect(() => {
    if (newsItems) {
      const fetchResults = async () => {
        const itemsWithResults = await Promise.all(
          newsItems.map(async (item) => {
            try {
              const results = await fetch(
                `/api/news-items/${item.id}/results`,
                {
                  headers: {
                    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
                  },
                }
              ).then(r => r.json());
              return { ...item, processing_results: results };
            } catch {
              return { ...item, processing_results: [] };
            }
          })
        );
        setNewsItemsWithResults(itemsWithResults);
      };
      fetchResults();
    }
  }, [newsItems]);

  const handleRowClick = (item: NewsItem) => {
    setSelectedItem(item);
    onOpen();
  };

  const handlePrevious = () => {
    if (skip > 0) {
      setSkip(Math.max(0, skip - limit));
    }
  };

  const handleNext = () => {
    if (newsItems && newsItems.length === limit) {
      setSkip(skip + limit);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString();
  };

  const getSourceName = (sourceId: number) => {
    const source = sources?.find((s) => Number(s.id) === sourceId);
    return source?.name || `#${sourceId}`;
  };

  const getProcessingStatus = (item: NewsItem) => {
    if (!item.processing_results || item.processing_results.length === 0) {
      return { icon: InfoIcon, color: 'gray', text: 'Not processed', count: 0 };
    }

    const processed = item.processing_results.filter(r => r.processed).length;
    const total = item.processing_results.length;
    const anyPositive = item.processing_results.some(r => r.result === true);

    if (processed === 0) {
      return { icon: InfoIcon, color: 'gray', text: 'Pending', count: total };
    } else if (processed < total) {
      return { icon: WarningIcon, color: 'yellow', text: `Processing ${processed}/${total}`, count: total };
    } else if (anyPositive) {
      return { icon: CheckCircleIcon, color: 'green', text: `Matched`, count: total };
    } else {
      return { icon: InfoIcon, color: 'blue', text: `Processed`, count: total };
    }
  };

  const getAIOutput = (item: NewsItem) => {
    if (!item.processing_results || item.processing_results.length === 0) {
      return '-';
    }

    const results = item.processing_results
      .filter(r => r.processed && r.result === true)
      .map(r => r.ai_response?.thinking || 'Match')
      .join('; ');

    return results || 'No matches';
  };

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={6} align="stretch">
        <Box>
          <Alert status="warning" mb={4}>
            <AlertIcon />
            Testing Feature - News Items Database Viewer
          </Alert>
          <Heading size="lg" mb={4}>
            News Items
          </Heading>
        </Box>

        <HStack spacing={4} wrap="wrap">
          <Box>
            <Text fontSize="sm" mb={1} fontWeight="medium">
              Source
            </Text>
            <Select
              placeholder="All Sources"
              value={sourceId || ''}
              onChange={(e) =>
                setSourceId(e.target.value ? Number(e.target.value) : undefined)
              }
              width="200px"
            >
              {sources?.map((source) => (
                <option key={source.id} value={source.id}>
                  {source.name}
                </option>
              ))}
            </Select>
          </Box>
        </HStack>

        {isLoading && (
          <Center py={10}>
            <Spinner size="xl" />
          </Center>
        )}

        {error && (
          <Alert status="error">
            <AlertIcon />
            Error loading news items
          </Alert>
        )}

        {!isLoading && newsItemsWithResults && (
          <>
            <Box overflowX="auto">
              <Table variant="simple">
                <Thead>
                  <Tr>
                    <Th>ID</Th>
                    <Th>Title</Th>
                    <Th>Source</Th>
                    <Th>Published</Th>
                    <Th>Status</Th>
                    <Th maxW="300px">AI Output</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {newsItemsWithResults.map((item) => {
                    const status = getProcessingStatus(item);
                    return (
                      <Tr
                        key={item.id}
                        onClick={() => handleRowClick(item)}
                        cursor="pointer"
                        _hover={{ bg: 'gray.50' }}
                      >
                        <Td>{item.id}</Td>
                        <Td maxW="300px" isTruncated>
                          {item.title || '(No title)'}
                        </Td>
                        <Td>{getSourceName(item.source_id)}</Td>
                        <Td>{formatDate(item.published_at)}</Td>
                        <Td>
                          <Tooltip label={status.text}>
                            <HStack spacing={1}>
                              <Icon as={status.icon} color={`${status.color}.500`} />
                              {status.count > 0 && (
                                <Badge colorScheme={status.color} fontSize="xs">
                                  {status.count}
                                </Badge>
                              )}
                            </HStack>
                          </Tooltip>
                        </Td>
                        <Td maxW="300px" isTruncated>
                          <Text fontSize="sm" color="gray.600">
                            {getAIOutput(item)}
                          </Text>
                        </Td>
                      </Tr>
                    );
                  })}
                </Tbody>
              </Table>
            </Box>

            {newsItemsWithResults.length === 0 && (
              <Center py={10}>
                <Text color="gray.500">No news items found</Text>
              </Center>
            )}

            <HStack justify="space-between" pt={4}>
              <Text fontSize="sm" color="gray.600">
                Showing {skip + 1}-{skip + newsItemsWithResults.length}
              </Text>
              <HStack>
                <Button
                  size="sm"
                  onClick={handlePrevious}
                  isDisabled={skip === 0}
                >
                  Previous
                </Button>
                <Button
                  size="sm"
                  onClick={handleNext}
                  isDisabled={newsItemsWithResults.length < limit}
                >
                  Next
                </Button>
              </HStack>
            </HStack>
          </>
        )}
      </VStack>

      {selectedItem && (
        <NewsItemDetail
          item={selectedItem}
          sourceName={getSourceName(selectedItem.source_id)}
          isOpen={isOpen}
          onClose={onClose}
        />
      )}
    </Container>
  );
}

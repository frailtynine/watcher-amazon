import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Heading,
  Text,
  Grid,
  GridItem,
  VStack,
  HStack,
  Link,
  Spinner,
  Center,
  Divider,
  Button,
} from '@chakra-ui/react';
import { ArrowBackIcon, ExternalLinkIcon } from '@chakra-ui/icons';
import { useGetNewspaperQuery, useGetSourcesQuery } from '../../services/api';
import type { NewspaperItem, Source } from '../../types';

const truncate = (text: string | null, max: number): string => {
  if (!text) return '';
  return text.length > max ? text.slice(0, max) + '…' : text;
};

const formatDate = (iso: string) =>
  new Date(iso).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

interface NewsCardProps {
  item: NewspaperItem;
  sources: Source[];
  variant: 'large' | 'medium' | 'small';
}

const NewsCard = ({ item, sources, variant }: NewsCardProps) => {
  const source = sources.find((s) => Number(s.id) === item.source_id);
  const sourceName = source?.name ?? `Source #${item.source_id}`;

  return (
    <Box
      borderWidth="1px"
      borderRadius="md"
      p={4}
      bg="white"
      h="100%"
      display="flex"
      flexDirection="column"
    >
      <Link
        href={item.url ?? '#'}
        isExternal
        fontWeight="bold"
        fontSize={variant === 'large' ? 'xl' : variant === 'medium' ? 'md' : 'sm'}
        lineHeight="1.4"
        mb={2}
        _hover={{ color: 'blue.600', textDecoration: 'none' }}
        fontFamily="Georgia, serif"
      >
        {item.title}
        <ExternalLinkIcon mx="4px" boxSize={3} />
      </Link>

      {variant !== 'small' && (
        <Text fontSize="sm" color="gray.700" flex="1" mb={3}>
          {truncate(item.content, variant === 'large' ? 400 : 200)}
        </Text>
      )}

      <HStack fontSize="xs" color="gray.400" mt="auto" spacing={2} flexWrap="wrap">
        <Text fontWeight="medium" color="gray.600">
          {sourceName}
        </Text>
        {item.published_at && (
          <>
            <Text>·</Text>
            <Text>{formatDate(item.published_at)}</Text>
          </>
        )}
      </HStack>
    </Box>
  );
};

interface NewspaperRowProps {
  items: NewspaperItem[];
  sources: Source[];
}

const NewspaperRow = ({ items, sources }: NewspaperRowProps) => {
  if (items.length === 1) {
    return <NewsCard item={items[0]} sources={sources} variant="large" />;
  }

  if (items.length === 2) {
    return (
      <Grid templateColumns="1fr 1fr" gap={4}>
        {items.map((item, i) => (
          <GridItem key={i}>
            <NewsCard item={item} sources={sources} variant="medium" />
          </GridItem>
        ))}
      </Grid>
    );
  }

  return (
    <Grid templateColumns={`repeat(${items.length}, 1fr)`} gap={3}>
      {items.map((item, i) => (
        <GridItem key={i}>
          <NewsCard item={item} sources={sources} variant="small" />
        </GridItem>
      ))}
    </Grid>
  );
};

export const NewspaperPage = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const {
    data: newspaper,
    isLoading,
    isError,
  } = useGetNewspaperQuery(Number(taskId));
  const { data: sources = [] } = useGetSourcesQuery();

  if (isLoading) {
    return (
      <Center h="60vh">
        <Spinner size="xl" />
      </Center>
    );
  }

  if (isError || !newspaper) {
    return (
      <Center h="60vh">
        <VStack spacing={4}>
          <Text fontSize="lg" color="gray.500">
            No newspaper available for this task yet.
          </Text>
          <Button leftIcon={<ArrowBackIcon />} onClick={() => navigate(-1)}>
            Go back
          </Button>
        </VStack>
      </Center>
    );
  }

  const rows = Object.entries(newspaper.body)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([, items]) => items as NewspaperItem[]);

  return (
    <Box bg="gray.50" minH="100vh" py={8}>
      <Container maxW="4xl">
        <VStack align="stretch" spacing={0}>
          <Button
            leftIcon={<ArrowBackIcon />}
            variant="ghost"
            size="sm"
            alignSelf="flex-start"
            mb={4}
            onClick={() => navigate(-1)}
          >
            Back
          </Button>

          <Box textAlign="center" mb={6}>
            <Heading
              size="2xl"
              fontFamily="Georgia, serif"
              letterSpacing="-0.5px"
            >
              {newspaper.title}
            </Heading>
            <Text color="gray.500" fontSize="sm" mt={2}>
              Updated {new Date(newspaper.updated_at).toLocaleString()}
            </Text>
          </Box>

          <Divider borderColor="gray.800" borderWidth="2px" mb={2} />
          <Divider borderColor="gray.800" mb={6} />

          {rows.length === 0 ? (
            <Center py={12}>
              <Text color="gray.500">No news items in this edition yet.</Text>
            </Center>
          ) : (
            <VStack spacing={0} align="stretch">
              {rows.map((items, i) => (
                <Box key={i}>
                  <NewspaperRow items={items} sources={sources} />
                  {i < rows.length - 1 && (
                    <Divider borderColor="gray.300" my={6} />
                  )}
                </Box>
              ))}
            </VStack>
          )}
        </VStack>
      </Container>
    </Box>
  );
};

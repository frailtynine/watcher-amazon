import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Center,
  Container,
  Divider,
  Flex,
  Grid,
  GridItem,
  Heading,
  HStack,
  Link,
  Spinner,
  Text,
  VStack,
} from '@chakra-ui/react';
import { ExternalLinkIcon } from '@chakra-ui/icons';
import {
  useGetCurrentUserQuery,
  useGetPublicFrontpageNewspaperQuery,
  useLogoutMutation,
} from '../../services/api';
import type { NewspaperItem } from '../../types';

const truncate = (text: string | null, max: number): string => {
  if (!text) return '';
  return text.length > max ? text.slice(0, max) + '…' : text;
};

const formatDate = (iso: string | null): string => {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

interface NewsCardProps {
  item: NewspaperItem;
  variant: 'large' | 'medium' | 'small';
}

const NewsCard = ({ item, variant }: NewsCardProps) => {
  const title = item.link ? (
    <Link href={item.link} isExternal color="inherit" _hover={{ textDecoration: 'underline' }}>
      {item.title} <ExternalLinkIcon mx="2px" boxSize={3} />
    </Link>
  ) : item.title;

  return (
    <Box borderWidth="1px" borderRadius="md" p={4} bg="white" h="100%" display="flex" flexDirection="column">
      <Text
        fontWeight="bold"
        fontSize={variant === 'large' ? 'xl' : variant === 'medium' ? 'md' : 'sm'}
        lineHeight="1.4"
        mb={2}
        fontFamily="Georgia, serif"
      >
        {title}
      </Text>

      {variant !== 'small' && (
        <Text fontSize="sm" color="gray.700" flex="1" mb={3}>
          {truncate(item.summary, variant === 'large' ? 400 : 200)}
        </Text>
      )}

      {(item.source_name || item.pub_date) && (
        <Text fontSize="xs" color="gray.400" mt="auto">
          {[item.source_name, item.pub_date ? formatDate(item.pub_date) : null]
            .filter(Boolean)
            .join(' · ')}
        </Text>
      )}
    </Box>
  );
};

const NewspaperRow = ({ items }: { items: NewspaperItem[] }) => {
  if (items.length <= 2) {
    return (
      <Grid
        templateColumns={{ base: '1fr', md: items.length === 2 ? '1fr 1fr' : '1fr' }}
        gap={4}
      >
        {items.map((item, i) => (
          <GridItem key={i}>
            <NewsCard item={item} variant="medium" />
          </GridItem>
        ))}
      </Grid>
    );
  }

  return (
    <>
      <Box
        display={{ base: 'block', md: 'none' }}
        borderWidth="1px"
        borderRadius="md"
        p={4}
        bg="white"
      >
        <VStack align="stretch" spacing={3}>
          {items.map((item, i) => (
            <Box key={i}>
              <Text fontWeight="bold" fontSize="sm" fontFamily="Georgia, serif" lineHeight="1.4">
                {item.link ? (
                  <Link href={item.link} isExternal color="inherit" _hover={{ textDecoration: 'underline' }}>
                    {item.title} <ExternalLinkIcon mx="2px" boxSize={3} />
                  </Link>
                ) : (
                  item.title
                )}
              </Text>
              {i < items.length - 1 && <Divider mt={3} borderColor="gray.200" />}
            </Box>
          ))}
        </VStack>
      </Box>

      <Grid display={{ base: 'none', md: 'grid' }} templateColumns={`repeat(${items.length}, 1fr)`} gap={3}>
        {items.map((item, i) => (
          <GridItem key={i}>
            <NewsCard item={item} variant="small" />
          </GridItem>
        ))}
      </Grid>
    </>
  );
};

export const PublicFrontPage = () => {
  const navigate = useNavigate();
  const token = localStorage.getItem('access_token');
  const hasToken = Boolean(token);

  const { data: user } = useGetCurrentUserQuery(undefined, { skip: !hasToken });
  const [logout] = useLogoutMutation();
  const { data: newspaper, isLoading: isLoadingNewspaper } = useGetPublicFrontpageNewspaperQuery();

  const handleLogout = async () => {
    try {
      await logout().unwrap();
    } catch {
    } finally {
      localStorage.removeItem('access_token');
      navigate('/');
    }
  };

  const rowMap = new Map<number, NewspaperItem[]>();
  if (newspaper?.body?.rows) {
    for (const item of newspaper.body.rows) {
      const rowNum = item.position[0];
      if (!rowMap.has(rowNum)) rowMap.set(rowNum, []);
      rowMap.get(rowNum)!.push(item);
    }
  }
  const rows = [...rowMap.entries()]
    .sort(([a], [b]) => a - b)
    .map(([, items]) => items.sort((a, b) => a.position[1] - b.position[1]));

  const isLoading = isLoadingNewspaper;

  return (
    <Box bg="gray.50" minH="100vh" px={{ base: 2, md: 4 }} py={{ base: 4, md: 6 }}>
      <Container maxW="3xl" px={{ base: 0, md: 0 }}>
        <Flex justify="flex-end" mb={4}>
          {user ? (
            <HStack spacing={3}>
              <Text fontSize="sm" color="gray.700">{user.email}</Text>
              <Button size="sm" variant="outline" onClick={handleLogout}>
                Logout
              </Button>
            </HStack>
          ) : (
            <Button size="sm" colorScheme="blue" onClick={() => navigate('/login')}>
              Login
            </Button>
          )}
        </Flex>

        <Box
          bg="yellow.200"
          color="black"
          borderRadius="lg"
          px={4}
          py={3}
          mb={6}
          fontWeight="medium"
        >
          This page is an AI-generated digest of recent news about the war in Iran and may contain inaccuracies. Powered by Amazon Nova.
        </Box>

        {isLoading && (
          <Center h="60vh">
            <Spinner size="xl" />
          </Center>
        )}

        {!isLoading && (!newspaper || rows.length === 0) && (
          <Center h="60vh">
            <VStack spacing={3}>
              <Heading size="md" color="gray.600">No frontpage available yet</Heading>
              <Text color="gray.500">
                No active newspaper with content is currently available.
              </Text>
            </VStack>
          </Center>
        )}

        {!isLoading && newspaper && rows.length > 0 && (
          <VStack align="stretch" spacing={0}>
            <Box textAlign="center" mb={6}>
              <Heading size="2xl" fontFamily="Georgia, serif" letterSpacing="-0.5px">
                War in Iran: Daily Digest 
              </Heading>
              <Text color="gray.500" fontSize="sm" mt={2}>
                Updated {new Date(newspaper.updated_at).toLocaleString()}
              </Text>
            </Box>

            <Divider borderColor="gray.800" borderWidth="2px" mb={2} />
            <Divider borderColor="gray.800" mb={6} />

            <VStack spacing={0} align="stretch">
              {rows.map((items, i) => (
                <Box key={i}>
                  <NewspaperRow items={items} />
                  {i < rows.length - 1 && <Divider borderColor="gray.300" my={6} />}
                </Box>
              ))}
            </VStack>
          </VStack>
        )}
      </Container>
    </Box>
  );
};

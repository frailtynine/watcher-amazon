import { useState } from 'react';
import {
  Box,
  Button,
  Container,
  FormControl,
  FormLabel,
  Input,
  VStack,
  Heading,
  Text,
  useToast,
  Link as ChakraLink,
} from '@chakra-ui/react';
import { Link, useNavigate } from 'react-router-dom';
import { useLoginMutation } from '@/services/api';

export const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [login, { isLoading }] = useLoginMutation();
  const toast = useToast();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const result = await login({ username: email, password }).unwrap();
      localStorage.setItem('access_token', result.access_token);
      toast({
        title: 'Login successful',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      navigate('/tasks');
    } catch (error: any) {
      toast({
        title: 'Login failed',
        description: error?.data?.detail || 'Invalid credentials',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  return (
    <Container maxW="md" py={20}>
      <Box
        bg="white"
        p={8}
        borderRadius="lg"
        boxShadow="lg"
      >
        <VStack spacing={6} align="stretch">
          <Heading size="lg" textAlign="center">
            NewsWatcher
          </Heading>
          <Text textAlign="center" color="gray.600">
            Sign in to your account
          </Text>

          <form onSubmit={handleSubmit}>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Email</FormLabel>
                <Input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Password</FormLabel>
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                />
              </FormControl>

              <Button
                type="submit"
                colorScheme="blue"
                width="full"
                isLoading={isLoading}
              >
                Sign In
              </Button>

              <Text textAlign="center" fontSize="sm">
                Don't have an account?{' '}
                <ChakraLink as={Link} to="/signup" color="blue.500">
                  Sign Up
                </ChakraLink>
              </Text>
            </VStack>
          </form>
        </VStack>
      </Box>
    </Container>
  );
};

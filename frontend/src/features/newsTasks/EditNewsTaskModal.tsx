import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  VStack,
  HStack,
  Divider,
  Heading,
  useToast,
  FormErrorMessage,
  useDisclosure,
  Box,
  Text,
} from '@chakra-ui/react';
import { AddIcon } from '@chakra-ui/icons';
import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  useUpdateNewsTaskMutation,
  useGetTaskSourcesQuery,
  useGetSourcesQuery,
} from '../../services/api';
import type { NewsTask } from '../../types';
import { SourcesList } from '../sources/SourcesList';
import { AddSourceModal } from '../sources/AddSourceModal';

interface EditNewsTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  task: NewsTask;
}

export const EditNewsTaskModal = ({
  isOpen,
  onClose,
  task,
}: EditNewsTaskModalProps) => {
  const navigate = useNavigate();
  const [updateTask, { isLoading }] = useUpdateNewsTaskMutation();
  const { data: associations } = useGetTaskSourcesQuery(task.id);
  const { data: allSources } = useGetSourcesQuery();
  const toast = useToast();

  const addSourceModal = useDisclosure();

  const [name, setName] = useState(task.name);
  const [prompt, setPrompt] = useState(task.prompt);
  const [errors, setErrors] = useState<{
    name?: string;
    prompt?: string;
  }>({});

  useEffect(() => {
    setName(task.name);
    setPrompt(task.prompt);
  }, [task]);

  const validate = () => {
    const newErrors: typeof errors = {};

    if (!name.trim()) {
      newErrors.name = 'Task name is required';
    } else if (name.length < 3) {
      newErrors.name = 'Task name must be at least 3 characters';
    } else if (name.length > 100) {
      newErrors.name = 'Task name must be less than 100 characters';
    }

    if (!prompt.trim()) {
      newErrors.prompt = 'AI prompt is required';
    } else if (prompt.length < 10) {
      newErrors.prompt = 'Prompt must be at least 10 characters';
    } else if (prompt.length > 1000) {
      newErrors.prompt = 'Prompt must be less than 1000 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) {
      return;
    }

    try {
      await updateTask({
        id: task.id,
        data: {
          name: name.trim(),
          prompt: prompt.trim(),
        },
      }).unwrap();

      toast({
        title: 'Task updated',
        status: 'success',
        duration: 2000,
      });

      onClose();
    } catch (error) {
      toast({
        title: 'Failed to update task',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const sources = useMemo(() => {
    if (!associations || !allSources) return [];
    const sourceIds = associations.map((a) => a.source_id);
    return allSources.filter((s) => sourceIds.includes(Number(s.id)));
  }, [associations, allSources]);

  return (
    <>
      <Modal isOpen={isOpen} onClose={onClose} size="2xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Edit: {task.name}</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={6} align="stretch">
              <VStack spacing={4}>
                <FormControl isInvalid={!!errors.name} isRequired>
                  <FormLabel>Task Name</FormLabel>
                  <Input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                  <FormErrorMessage>{errors.name}</FormErrorMessage>
                </FormControl>

                <FormControl isInvalid={!!errors.prompt} isRequired>
                  <FormLabel>AI Prompt</FormLabel>
                  <Textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    rows={4}
                  />
                  <FormErrorMessage>{errors.prompt}</FormErrorMessage>
                </FormControl>
              </VStack>

              <Divider />

              <Box>
                <HStack justify="space-between" mb={4}>
                  <Heading size="sm">
                    RSS Feeds ({sources.length})
                  </Heading>
                  <Button
                    leftIcon={<AddIcon />}
                    size="sm"
                    colorScheme="blue"
                    onClick={addSourceModal.onOpen}
                  >
                    Add Feed
                  </Button>
                </HStack>

                {sources.length === 0 ? (
                  <Box
                    p={6}
                    bg="gray.50"
                    borderRadius="md"
                    textAlign="center"
                  >
                    <Text color="gray.500" fontSize="sm">
                      No RSS feeds added yet
                    </Text>
                  </Box>
                ) : (
                  <SourcesList sources={sources} taskId={task.id} />
                )}
              </Box>
            </VStack>
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button
              colorScheme="teal"
              variant="outline"
              mr={3}
              onClick={() => {
                onClose();
                navigate(`/newspaper/${task.id}`);
              }}
            >
              📰 View Newspaper
            </Button>
            <Button
              colorScheme="blue"
              onClick={handleSubmit}
              isLoading={isLoading}
            >
              Save Changes
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      <AddSourceModal
        isOpen={addSourceModal.isOpen}
        onClose={addSourceModal.onClose}
        taskId={task.id}
      />
    </>
  );
};
